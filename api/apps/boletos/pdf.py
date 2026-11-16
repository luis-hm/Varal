"""Bounded, offline extraction of structured fields from boleto PDFs."""

import logging
import re
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from io import BytesIO

import pdfplumber
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError
from pdfminer.pdftypes import resolve1
from pdfminer.psparser import PSLiteral

from apps.boletos.parser import ErroValidacao, ler

MAX_BYTES = 5 * 1024 * 1024
MAX_PAGES = 20
MAX_CHARS = 200_000
MAX_BENEFICIARIO = 200


@dataclass(frozen=True)
class Candidato:
    tipo: str
    codigo: str
    valor_centavos: int | None
    vencimento: date | None
    vencimentos_possiveis: tuple[date, ...]
    avisos: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResultadoPDF:
    estado: str  # lido, conferencia_manual, invalido
    candidatos: tuple[Candidato, ...] = ()
    valor_centavos: int | None = None
    vencimento: date | None = None
    data_emissao: date | None = None
    beneficiario: str | None = None
    valor_textual_centavos: int | None = None
    vencimento_textual: date | None = None
    avisos: tuple[str, ...] = field(default_factory=tuple)


_LOG_FACTORY_LOCK = threading.RLock()


@contextmanager
def _proteger_logs_pdf():
    # Record factory is process-global; only redact this thread's dependency records.
    # Serialize these contexts and restore the exact previously configured factory.
    with _LOG_FACTORY_LOCK:
        original = logging.getLogRecordFactory()
        owner = threading.get_ident()

        def safe_factory(*args, **kwargs):
            record = original(*args, **kwargs)
            if threading.get_ident() == owner and (
                record.name == "pdfminer"
                or record.name.startswith("pdfminer.")
                or record.name == "pdfplumber"
                or record.name.startswith("pdfplumber.")
            ):
                record.msg = "Aviso da biblioteca de PDF omitido para proteger dados do documento."
                record.args = ()
                record.exc_info = None
                record.exc_text = None
                record.stack_info = None
            return record

        logging.setLogRecordFactory(safe_factory)
        try:
            yield
        finally:
            logging.setLogRecordFactory(original)


def _linhas_candidatas(texto):
    # Join only adjacent, entirely numeric lines; never take a subrange of a
    # longer run. Two complete adjacent codes remain two separate candidates.
    lines = texto.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if not re.fullmatch(r"[ 0-9.]+", line) or not any(c in "0123456789" for c in line):
            yield line
            i += 1
            continue
        group = []
        while (
            i < len(lines)
            and re.fullmatch(r"[ 0-9.]+", lines[i])
            and any(c in "0123456789" for c in lines[i])
        ):
            group.append(lines[i])
            i += 1
        if all(sum(c in "0123456789" for c in part) in (47, 48) for part in group):
            yield from group
        else:
            yield " ".join(group)


def _estrutura_paginas_valida(pdf):
    pages = resolve1(pdf.doc.catalog.get("Pages"))
    return (
        isinstance(pages, dict)
        and isinstance(pages.get("Type"), PSLiteral)
        and pages["Type"].name == "Pages"
        and isinstance(resolve1(pages.get("Kids")), list)
        and type(resolve1(pages.get("Count"))) is int
        and resolve1(pages.get("Count")) >= 0
    )


def _texto_seguro(texto, limite):
    if not isinstance(texto, str) or len(texto) > limite or "\x00" in texto:
        return False
    try:
        texto.encode("utf-8", errors="strict")
    except UnicodeError:
        return False
    return True


def _campo(texto, padrao):
    valores = re.findall(padrao, texto, re.IGNORECASE | re.MULTILINE)
    # Disagreement or repetition with distinct values cannot be attributed safely.
    distintos = list(dict.fromkeys(v.strip() for v in valores))
    return distintos[0] if len(distintos) == 1 else None


def _data(texto, rotulo):
    achado = _campo(
        texto, rf"^[ \t]*(?:{rotulo})[ \t]*:?[ \t]*([0-9]{{2}}/[0-9]{{2}}/[0-9]{{4}})[ \t]*$"
    )
    if achado is None:
        return None
    try:
        dia, mes, ano = map(int, achado.split("/"))
        return date(ano, mes, dia)
    except ValueError:
        return None


def _valor(texto):
    achado = _campo(
        texto,
        r"^[ \t]*(?:valor[ \t]+(?:do[ \t]+documento|cobrado))[ \t]*:?[ \t]*"
        r"(?:R\$[ \t]*)?((?:[0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+),[0-9]{2})[ \t]*$",
    )
    if achado is None or len(achado) > 20:
        return None
    valor = int(Decimal(achado.replace(".", "").replace(",", ".")) * 100)
    return valor if 0 < valor <= 99_999_999_999 else None


def _analisar_texto(texto):
    if not _texto_seguro(texto, MAX_CHARS):
        return ResultadoPDF(
            "conferencia_manual",
            avisos=("Texto não pôde ser processado com segurança; confira manualmente.",),
        )
    emission = _data(texto, r"data\s+do\s+documento")
    due_text = _data(texto, r"(?:data\s+de\s+)?vencimento")
    value_text = _valor(texto)
    beneficiary = _campo(texto, r"^[ \t]*benefici[aá]rio[ \t]*:?[ \t]*([^\r\n]+?)[ \t]*$")
    if beneficiary is not None and (
        not _texto_seguro(beneficiary, MAX_BENEFICIARIO) or any(ord(c) < 32 for c in beneficiary)
    ):
        beneficiary = None
    encontrados = {}
    for line in _linhas_candidatas(texto):
        # Consider the whole numeric run, never a valid-looking substring.
        for match in re.finditer(
            r"(?<![0-9A-Za-z.])[0-9][0-9 .]*[0-9](?![0-9A-Za-z.])", line, re.ASCII
        ):
            try:
                result = ler(codigo=match.group())
            except ErroValidacao:
                continue
            if result.tipo not in ("boleto_bancario", "boleto_arrecadacao"):
                continue
            # Revalidate every structured string leaving this non-DRF boundary.
            if (
                not isinstance(result.codigo, str)
                or not re.fullmatch(r"[0-9]{47,48}", result.codigo)
                or not isinstance(result.avisos, (list, tuple))
                or len(result.avisos) > 20
                or not isinstance(result.vencimentos_possiveis, (list, tuple))
                or len(result.vencimentos_possiveis) > 2
                or any(type(d) is not date for d in result.vencimentos_possiveis)
                or (result.vencimento is not None and type(result.vencimento) is not date)
                or (
                    result.valor_centavos is not None
                    and (
                        type(result.valor_centavos) is not int
                        or not 0 < result.valor_centavos <= 99_999_999_999
                    )
                )
            ):
                continue
            strings = [result.tipo, result.codigo, *result.avisos]
            if any(not _texto_seguro(s, 4096) for s in strings):
                continue
            encontrados[result.codigo] = Candidato(
                result.tipo,
                result.codigo,
                result.valor_centavos,
                result.vencimento,
                tuple(result.vencimentos_possiveis),
                tuple(result.avisos),
            )
    candidatos = tuple(encontrados.values())
    avisos = []
    valor = value_text
    vencimento = due_text
    if len(candidatos) > 1:
        avisos.append("Mais de uma linha válida encontrada; escolha a cobrança e confira os dados.")
        # Text cannot be attributed to one of multiple documents.
        return ResultadoPDF("conferencia_manual", candidatos=candidatos, avisos=tuple(avisos))
    if candidatos:
        candidato = candidatos[0]
        avisos.extend(candidato.avisos)
        if candidato.valor_centavos is not None:
            valor = candidato.valor_centavos
            if value_text is not None and value_text != valor:
                avisos.append("Valor do texto diverge do código; prevalece o código.")
        if candidato.vencimentos_possiveis:
            if due_text in candidato.vencimentos_possiveis:
                vencimento = due_text
            else:
                vencimento = candidato.vencimento
                if due_text is not None:
                    avisos.append(
                        "Vencimento do texto diverge do código; confira os ciclos indicados."
                    )
        estado = "lido"
    else:
        estado = "conferencia_manual"
        avisos.append("Nenhuma linha digitável válida encontrada; confira ou informe manualmente.")
    return ResultadoPDF(
        estado,
        candidatos,
        valor,
        vencimento,
        emission,
        beneficiary,
        value_text,
        due_text,
        tuple(avisos),
    )


def extrair_pdf(arquivo):
    """Extract safe fields without network, filesystem writes or account changes."""
    if not isinstance(arquivo, bytes) or not arquivo or len(arquivo) > MAX_BYTES:
        return ResultadoPDF("invalido", avisos=("Arquivo vazio, inválido ou acima de 5 MiB.",))
    if not arquivo.startswith(b"%PDF-") or b"%%EOF" not in arquivo[-1024:]:
        return ResultadoPDF("invalido", avisos=("Arquivo não é um PDF válido.",))
    try:
        with _proteger_logs_pdf(), BytesIO(arquivo) as stream:
            pdf = pdfplumber.open(stream)
            if not _estrutura_paginas_valida(pdf):
                return ResultadoPDF("invalido", avisos=("Arquivo não é um PDF válido.",))
            with pdf:
                if len(pdf.pages) == 0:
                    return ResultadoPDF("invalido", avisos=("PDF sem páginas.",))
                if len(pdf.pages) > MAX_PAGES:
                    return ResultadoPDF(
                        "conferencia_manual",
                        avisos=(
                            "PDF excede o limite de 20 páginas; "
                            "leitura não realizada integralmente.",
                        ),
                    )
                pages = []
                count = 0
                for page in pdf.pages:
                    text = page.extract_text() or ""
                    count += len(text)
                    if count > MAX_CHARS:
                        return ResultadoPDF(
                            "conferencia_manual",
                            avisos=(
                                "PDF excede o limite de texto; "
                                "leitura não realizada integralmente.",
                            ),
                        )
                    pages.append(text)
                return _analisar_texto("\n".join(pages))
    except Exception as exc:  # noqa: BLE001 -- untrusted PDF must remain recoverable
        # pdfplumber can wrap pdfminer exceptions, exposing them as __context__.
        cause = exc
        while cause is not None:
            if isinstance(cause, PDFPasswordIncorrect):
                return ResultadoPDF(
                    "conferencia_manual",
                    avisos=("PDF protegido por senha; confira os dados manualmente.",),
                )
            if isinstance(cause, PDFSyntaxError):
                return ResultadoPDF("invalido", avisos=("Arquivo não é um PDF válido.",))
            cause = cause.__cause__ or cause.__context__
        # Do not leak extracted text or exception contents in results or logs.
        return ResultadoPDF(
            "conferencia_manual",
            avisos=("Não foi possível ler o PDF; confira os dados manualmente.",),
        )
