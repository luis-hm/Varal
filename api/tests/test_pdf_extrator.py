from datetime import date
from io import BytesIO
from types import SimpleNamespace

from reportlab.lib.pdfencrypt import StandardEncryption
from reportlab.pdfgen import canvas

from apps.boletos import pdf as ex


def dv10(s):
    table = ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (0, 2, 4, 6, 8, 1, 3, 5, 7, 9))
    return str(-sum(table[(len(s) - i) % 2][int(ch)] for i, ch in enumerate(s)) % 10)


def dv11(s):
    rem = sum(int(c) * (2 + i % 8) for i, c in enumerate(s[::-1])) % 11
    return str({0: 1, 1: 1, 10: 1}.get(rem, 11 - rem))


def codigo(fator=1000, centavos=12345):
    head = "0019"
    rest = f"{fator:04d}{centavos:010d}1234567890123456789012345"
    bar = head + dv11(head + rest) + rest
    parts = [bar[:4] + bar[19:24], bar[24:34], bar[34:44]]
    return "".join(p + dv10(p) for p in parts) + bar[4] + bar[5:19]


def gerar_pdf(linhas, paginas=1, senha=None):
    out = BytesIO()
    enc = StandardEncryption(senha, ownerPassword="owner") if senha else None
    page = canvas.Canvas(out, pagesize=(1500, 900), encrypt=enc)
    for _ in range(paginas):
        for i, line in enumerate(linhas):
            page.drawString(30, 850 - i * 18, line)
        page.showPage()
    page.save()
    return out.getvalue()


def test_rn26_rn27_pdf_extrai_linha_metadados_e_repeticao():
    code = codigo()
    formatted = (
        code[:5]
        + "."
        + code[5:10]
        + " "
        + code[10:20]
        + code[20]
        + " "
        + code[21:32]
        + " "
        + code[32:]
    )
    pdf = gerar_pdf(
        [
            formatted,
            code,
            "Beneficiario: Empresa Exemplo",
            "Data do documento: 01/02/2025",
            "Vencimento: 22/02/2025",
            "Valor do documento: R$ 123,45",
        ]
    )
    result = ex.extrair_pdf(pdf)
    assert result.estado == "lido" and len(result.candidatos) == 1
    assert result.candidatos[0].codigo == code
    assert result.valor_centavos == 12345 and result.vencimento == date(2025, 2, 22)
    assert result.beneficiario == "Empresa Exemplo" and result.data_emissao == date(2025, 2, 1)


def test_rn27_rn28_codigo_prevalece():
    result = ex.extrair_pdf(
        gerar_pdf([codigo(), "Vencimento: 25/02/2025", "Valor do documento: R$ 90,00"])
    )
    assert result.valor_centavos == 12345 and result.vencimento == date(2025, 2, 22)
    assert result.valor_textual_centavos == 9000 and result.vencimento_textual == date(2025, 2, 25)
    assert any("Valor do texto diverge" in a for a in result.avisos)
    assert any("Vencimento do texto diverge" in a for a in result.avisos)


def test_rn27_fator_legado_compativel_e_sugerido():
    result = ex.extrair_pdf(gerar_pdf([codigo(), "Vencimento: 03/07/2000"]))
    assert result.vencimento == date(2000, 7, 3)
    assert result.candidatos[0].vencimentos_possiveis == (date(2025, 2, 22), date(2000, 7, 3))


def test_rn26_multiplos_codigos_exigem_escolha_sem_metadados_desvinculados():
    result = ex.extrair_pdf(gerar_pdf([codigo(), codigo(1001), "Beneficiario: Empresa Exemplo"]))
    assert result.estado == "conferencia_manual" and len(result.candidatos) == 2
    assert (
        result.valor_centavos is None and result.vencimento is None and result.beneficiario is None
    )


def test_rn28_pdf_sem_texto_ou_codigo_invalido():
    for lines in ([], ["codigo 1234567890"], [codigo()[:-1] + "a"]):
        result = ex.extrair_pdf(gerar_pdf(lines))
        assert result.estado == "conferencia_manual" and not result.candidatos


def test_rn25_pdf_criptografado_retorna_manual():
    result = ex.extrair_pdf(gerar_pdf(["conteudo"], senha="senha"))
    assert result.estado == "conferencia_manual" and "senha" in result.avisos[0]


def test_rn25_limites_e_pdf_falso():
    for raw in (b"", b"nao pdf", b"%PDF-1.7\nfalso\n%%EOF", b"%PDF-" + b"x" * ex.MAX_BYTES):
        assert ex.extrair_pdf(raw).estado == "invalido"
    result = ex.extrair_pdf(gerar_pdf(["conteudo"], paginas=21))
    assert (
        result.estado == "conferencia_manual" and "não realizada integralmente" in result.avisos[0]
    )


def test_rn26_texto_excessivo_ou_inseguro(monkeypatch):
    for texto in ("\0" + codigo(), "\ud800" + codigo(), "x" * (ex.MAX_CHARS + 1)):
        result = ex._analisar_texto(texto)
        assert result.estado == "conferencia_manual" and not result.candidatos

    class FakePage:
        def extract_text(self):
            return "x" * (ex.MAX_CHARS + 1)

    class FakePDF:
        pages = (FakePage(),)
        doc = SimpleNamespace(
            catalog={"Pages": {"Type": ex.PSLiteral("Pages"), "Kids": [], "Count": 1}}
        )

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

    monkeypatch.setattr(ex.pdfplumber, "open", lambda _: FakePDF())
    result = ex.extrair_pdf(b"%PDF-1.7\n%%EOF")
    assert result.estado == "conferencia_manual" and "limite de texto" in result.avisos[0]


def test_rn26_beneficiario_extenso_e_multiplos_valores_nao_sao_devolvidos():
    result = ex._analisar_texto(
        "Beneficiario: " + ("A" * 201) + "\nValor cobrado: 1,00\nValor cobrado: 2,00"
    )
    assert result.beneficiario is None and result.valor_textual_centavos is None


def test_rn26_parser_com_retorno_inseguro_nao_persiste(monkeypatch):
    malicious = SimpleNamespace(
        tipo="boleto_bancario",
        codigo=codigo(),
        valor_centavos=1,
        vencimento=None,
        vencimentos_possiveis=(),
        avisos=["nao\x00seguro"],
    )
    monkeypatch.setattr(ex, "ler", lambda **kwargs: malicious)
    assert ex._analisar_texto(codigo()).candidatos == ()


def arrecadacao():
    data = "826" + "00000012345" + "12345678901234567890123456789"
    bar = data[:3] + dv10(data) + data[3:]
    return "".join(bar[i : i + 11] + dv10(bar[i : i + 11]) for i in range(0, 44, 11))


def test_rn10_pdf_arrecadacao_data_e_valor():
    result = ex.extrair_pdf(
        gerar_pdf([arrecadacao(), "Vencimento: 19/03/2026", "Valor cobrado: 10,00"])
    )
    assert result.candidatos[0].tipo == "boleto_arrecadacao"
    assert result.valor_centavos == 12345
    assert result.vencimento == date(2026, 3, 19)
    assert any("Valor do texto diverge" in a for a in result.avisos)


def test_rn26_limite_resultados_e_campos_tipados(monkeypatch):
    fields = {
        "tipo": "boleto_bancario",
        "codigo": codigo(),
        "valor_centavos": 1,
        "vencimento": None,
        "vencimentos_possiveis": (),
        "avisos": [],
    }
    for change in (
        {"codigo": "1" * 5000},
        {"valor_centavos": 10**50},
        {"vencimentos_possiveis": ("2025-01-01",)},
        {"avisos": ["a" * 4097]},
        {"avisos": ["\ud800"]},
    ):
        candidate = SimpleNamespace(**(fields | change))
        monkeypatch.setattr(ex, "ler", lambda candidate=candidate, **kwargs: candidate)
        assert ex._analisar_texto(codigo()).candidatos == ()


def test_rn25_catalogo_sem_arvore_de_paginas_e_invalido():
    original = gerar_pdf(["texto"])
    import re

    malformed, count = re.subn(
        rb"/Pages (\d+ \d+ R)",
        lambda m: b"/Pages " + b"(a)" + b" " * (len(m.group(1)) - 3),
        original,
        count=1,
    )
    assert count == 1 and len(malformed) == len(original)
    assert ex.extrair_pdf(malformed).estado == "invalido"


def test_rn26_linha_quebrada_em_pdf_real():
    code = codigo()
    result = ex.extrair_pdf(gerar_pdf([code[:32], code[32:]]))
    assert result.estado == "lido" and result.candidatos[0].codigo == code


def test_rn26_nao_recorta_sequencia_maior_em_uma_ou_varias_linhas():
    code = codigo()
    for lines in (
        [code + "1"],
        [code[:32], code[32:] + "1"],
        ["9" + code[:32], code[32:]],
        [code[:20], code[20:], "1"],
    ):
        result = ex.extrair_pdf(gerar_pdf(lines))
        assert result.estado == "conferencia_manual" and result.candidatos == ()


def test_rn26_pdf_logs_sanitizados_e_configuracao_restaurada(caplog):
    import logging

    original = logging.getLogRecordFactory()
    output = BytesIO()
    page = canvas.Canvas(output)
    page.addLiteral("(sensitive-test@example.com) g")
    page.drawString(30, 500, "texto normal")
    page.save()
    with caplog.at_level(logging.WARNING):
        result = ex.extrair_pdf(output.getvalue())
    assert result.estado == "conferencia_manual"
    assert any(record.name.startswith("pdfminer.") for record in caplog.records)
    assert "sensitive-test@example.com" not in caplog.text
    assert logging.getLogRecordFactory() is original


def test_rn26_fabrica_log_restaurada_mesmo_quando_biblioteca_falha(monkeypatch):
    import logging

    original = logging.getLogRecordFactory()

    def falha(*args, **kwargs):
        raise RuntimeError("informacao sensivel")

    monkeypatch.setattr(ex.pdfplumber, "open", falha)
    assert ex.extrair_pdf(b"%PDF-1.7\n%%EOF").estado == "conferencia_manual"
    assert logging.getLogRecordFactory() is original
