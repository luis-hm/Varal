"""Pure parsing of Brazilian payment codes. No network or framework dependencies."""

import binascii
import re
import uuid
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import Decimal


class ErroValidacao(ValueError):
    """Invalid payment code or Pix key."""


@dataclass(frozen=True)
class Resultado:
    tipo: str
    codigo: str | None = None
    chave_pix: str | None = None
    beneficiario: str | None = None
    valor_centavos: int | None = None
    vencimento: date | None = None
    avisos: list[str] = field(default_factory=list)
    vencimentos_possiveis: tuple[date, ...] = ()


def _mod10(s):
    total = 0
    for i, c in enumerate(reversed(s)):
        n = int(c) * (2 if i % 2 == 0 else 1)
        total += n // 10 + n % 10
    return (10 - total % 10) % 10


def _mod11(s, arrecadacao=False):
    total = sum(int(c) * (2 + i % 8) for i, c in enumerate(reversed(s)))
    resto = total % 11
    if arrecadacao:
        return 0 if resto in (0, 1) else 1 if resto == 10 else 11 - resto
    dv = 11 - resto
    return 1 if dv in (0, 10, 11) else dv


def _boleto(raw):
    if not re.fullmatch(r"[0-9. \t\r\n]+", raw, re.ASCII):
        raise ErroValidacao("Linha digitável contém caracteres inválidos.")
    s = re.sub(r"[. \t\r\n]", "", raw)
    if len(s) == 47:
        if s[3] != "9":
            raise ErroValidacao("Moeda do boleto inválida.")
        for start, end in ((0, 9), (10, 20), (21, 31)):
            if _mod10(s[start:end]) != int(s[end]):
                raise ErroValidacao("Dígito verificador do boleto inválido.")
        barra = s[:4] + s[32] + s[33:47] + s[4:9] + s[10:20] + s[21:31]
        if _mod11(barra[:4] + barra[5:]) != int(barra[4]):
            raise ErroValidacao("Dígito verificador geral do boleto inválido.")
        fator = int(s[33:37])
        avisos = []
        vencimento = None
        if fator:
            legado = date(1997, 10, 7) + timedelta(days=fator)
            if fator >= 1000:
                vencimento = date(2025, 2, 22) + timedelta(days=fator - 1000)
                avisos.append(
                    "Fator ambíguo entre ciclos; no ciclo anterior corresponde a "
                    f"{legado:%d/%m/%Y}. "
                    "Confira o vencimento no boleto."
                )
            else:
                vencimento = legado
        return Resultado(
            "boleto_bancario",
            codigo=s,
            valor_centavos=int(s[37:47]) or None,
            vencimento=vencimento,
            avisos=avisos,
            vencimentos_possiveis=(
                (vencimento, legado) if fator >= 1000 else (vencimento,) if fator else ()
            ),
        )
    if len(s) == 48 and s[0] == "8" and s[1] in "12345679" and s[2] in "6789":
        mod = _mod10 if s[2] in "67" else lambda v: _mod11(v, True)
        for start in range(0, 48, 12):
            if mod(s[start : start + 11]) != int(s[start + 11]):
                raise ErroValidacao("Dígito verificador da arrecadação inválido.")
        barra = "".join(s[i : i + 11] for i in range(0, 48, 12))
        if mod(barra[:3] + barra[4:]) != int(barra[3]):
            raise ErroValidacao("Dígito verificador geral da arrecadação inválido.")
        valor = (int(barra[4:15]) or None) if s[2] in "68" else None
        return Resultado("boleto_arrecadacao", codigo=s, valor_centavos=valor)
    raise ErroValidacao("Linha digitável deve ter 47 ou 48 dígitos válidos.")


def _tlv(data):
    out = {}
    pos = 0
    while pos < len(data):
        header = data[pos : pos + 4]
        if len(header) != 4 or not re.fullmatch(rb"[0-9]{4}", header):
            raise ErroValidacao("Estrutura Pix inválida.")
        key = header[:2].decode("ascii")
        length = int(header[2:])
        pos += 4
        if not length or pos + length > len(data) or key in out:
            raise ErroValidacao("Campo Pix duplicado, vazio ou truncado.")
        out[key] = data[pos : pos + length]
        pos += length
    return out


def _validar_location(value):
    # Only validate the encoded location. Do not dereference it.
    if len(value) > 77:
        raise ErroValidacao("Endereço Pix inválido.")
    match = re.fullmatch(
        rb"([A-Za-z0-9.-]+)/((?:[A-Za-z0-9._~!$&'()*+,;=/-]|%[0-9A-Fa-f]{2})+)",
        value,
    )
    if not match:
        raise ErroValidacao("Endereço Pix inválido.")
    host = match.group(1)
    labels = host.split(b".")
    if len(labels) < 2 or any(
        not re.fullmatch(rb"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
        for label in labels
    ):
        raise ErroValidacao("Endereço Pix inválido.")


def _pix(raw):
    try:
        data = raw.encode("utf-8")
        fields = _tlv(data)
        if not data.startswith(b"000201") or not re.fullmatch(rb"6304[0-9A-F]{4}", data[-8:]):
            raise ErroValidacao("Identificação ou CRC Pix inválido.")
        if int(data[-4:], 16) != binascii.crc_hqx(data[:-4], 0xFFFF):
            raise ErroValidacao("CRC Pix inválido.")
        if fields.get("00") != b"01" or fields.get("53") != b"986" or fields.get("58") != b"BR":
            raise ErroValidacao("Formato, moeda ou país Pix inválido.")
        if not re.fullmatch(rb"[0-9]{4}", fields.get("52", b"")):
            raise ErroValidacao("Categoria Pix inválida.")
        if fields.get("01", b"11") not in (b"11", b"12"):
            raise ErroValidacao("Método Pix inválido.")
        if not (1 <= len(fields.get("59", b"")) <= 25 and 1 <= len(fields.get("60", b"")) <= 15):
            raise ErroValidacao("Nome ou cidade Pix ausente ou inválido.")
        nome = fields["59"].decode("utf-8")
        fields["60"].decode("utf-8")
        contas = []
        for key, value in fields.items():
            if 26 <= int(key) <= 51:
                sub = _tlv(value)
                if sub.get("00", b"").lower() == b"br.gov.bcb.pix":
                    contas.append(sub)
        if len(contas) != 1:
            raise ErroValidacao("Identificador Pix ausente ou duplicado.")
        conta = contas[0]
        if bool(conta.get("01")) == bool(conta.get("25")):
            raise ErroValidacao("Chave ou URL Pix ausente ou ambígua.")
        if "62" not in fields or not _tlv(fields["62"]).get("05"):
            raise ErroValidacao("Identificador de transação Pix ausente.")
        txid = _tlv(fields["62"])["05"]
        dinamico = "25" in conta
        valor = None
        avisos = ["Dados do recebedor não foram verificados."]
        if dinamico:
            _validar_location(conta["25"])
            avisos.append("Pix dinâmico: endereço não consultado; informe valor e vencimento.")
        else:
            chave = conta["01"].decode("utf-8")
            if _chave(chave).chave_pix != chave:
                raise ErroValidacao("Chave Pix no código deve estar no formato canônico.")
            if txid != b"***" and not re.fullmatch(rb"[A-Za-z0-9]{1,25}", txid):
                raise ErroValidacao("Identificador de transação Pix inválido.")
            if "54" in fields:
                v = fields["54"].decode("ascii")
                if not re.fullmatch(r"[0-9]{1,10}(?:\.[0-9]{1,2})?", v):
                    raise ErroValidacao("Valor Pix inválido.")
                valor = int(Decimal(v) * 100)
                if valor == 0:
                    raise ErroValidacao("Valor Pix deve ser maior que zero.")
        return Resultado("pix", codigo=raw, beneficiario=nome, valor_centavos=valor, avisos=avisos)
    except (UnicodeError, ValueError) as exc:
        if isinstance(exc, ErroValidacao):
            raise
        raise ErroValidacao("Conteúdo Pix inválido.") from exc


def _cpf(s):
    if len(set(s)) == 1:
        return False
    for n in (9, 10):
        r = sum(int(c) * (n + 1 - i) for i, c in enumerate(s[:n])) * 10 % 11
        if (r if r < 10 else 0) != int(s[n]):
            return False
    return True


def _cnpj(s):
    if len(set(s)) == 1:
        return False
    for n, weights in (
        (12, (5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
        (13, (6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2)),
    ):
        r = sum((ord(c) - 48) * w for c, w in zip(s[:n], weights, strict=True)) % 11
        if (0 if r < 2 else 11 - r) != int(s[n]):
            return False
    return True


def _chave(raw):
    s = raw.strip()
    if len(s) > 77 or not s:
        raise ErroValidacao("Chave Pix inválida.")
    if re.fullmatch(r"(?:[0-9]{11}|[0-9]{3}\.[0-9]{3}\.[0-9]{3}-[0-9]{2})", s):
        s = re.sub(r"[.-]", "", s)
        if not _cpf(s):
            raise ErroValidacao("CPF inválido.")
    elif re.fullmatch(
        r"(?:[A-Za-z0-9]{12}[0-9]{2}|[A-Za-z0-9]{2}\.[A-Za-z0-9]{3}\.[A-Za-z0-9]{3}/[A-Za-z0-9]{4}-[0-9]{2})",
        s,
    ):
        s = re.sub(r"[./-]", "", s).upper()
        if not _cnpj(s):
            raise ErroValidacao("CNPJ inválido.")
    elif re.fullmatch(r"\+[1-9][0-9]{7,14}", s):
        pass
    elif (
        re.fullmatch(
            r"[A-Za-z0-9.!#$&\'*+/=?^_`{|}~-]+@[A-Za-z0-9](?:[A-Za-z0-9.-]*[A-Za-z0-9])?",
            s,
        )
        and ".." not in s
        and all(
            re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,61}[A-Za-z0-9])?", label)
            for label in s.split("@")[1].split(".")
        )
    ):
        s = s.lower()
    else:
        try:
            parsed = uuid.UUID(s)
            if str(parsed) != s.lower():
                raise ValueError
            s = str(parsed)
        except ValueError as exc:
            raise ErroValidacao("Chave Pix inválida.") from exc
    return Resultado(
        "pix",
        chave_pix=s,
        avisos=["Chave não consultada; existência e titularidade não verificadas."],
    )


def ler(*, codigo=None, chave_pix=None):
    """Return Resultado; raise ErroValidacao. Exactly one argument must be supplied."""
    if (codigo is None) == (chave_pix is None):
        raise ErroValidacao("Informe código ou chave Pix.")
    value = codigo if codigo is not None else chave_pix
    if not isinstance(value, str) or not value or len(value) > 4096:
        raise ErroValidacao("Entrada vazia ou maior que o limite.")
    if chave_pix is not None:
        return _chave(chave_pix)
    return _pix(codigo) if codigo.startswith("000201") else _boleto(codigo)
