import binascii
from datetime import date

import pytest

from apps.boletos.parser import ErroValidacao, _mod10, _mod11, ler

STATIC = (
    "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-426655440000"
    "5204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***63041D3D"
)
DYNAMIC = (
    "00020101021226700014br.gov.bcb.pix2548pix.example.com/8b3da2f39a4140d1a91abd9"
    "3113bd4415204000053039865802BR5913Fulano de Tal6008BRASILIA62070503***630464E4"
)


# Independent test fixture construction: barcode data and per-block check digits,
# using tables rather than parser functions.
def dv10(s):
    table = ((0, 1, 2, 3, 4, 5, 6, 7, 8, 9), (0, 2, 4, 6, 8, 1, 3, 5, 7, 9))
    return str(-sum(table[(len(s) - i) % 2][int(ch)] for i, ch in enumerate(s)) % 10)


def dv11(s, arrec=False):
    weights = [2, 3, 4, 5, 6, 7, 8, 9]
    rem = sum(int(x) * weights[i % 8] for i, x in enumerate(s[::-1])) % 11
    return str(
        {0: 0, 1: 0, 10: 1}.get(rem, 11 - rem) if arrec else {0: 1, 1: 1, 10: 1}.get(rem, 11 - rem)
    )


def bancario(fator):
    # Synthetic beneficiary-independent bank barcode.
    head = "0019"
    rest = f"{fator:04d}" + "0000012345" + "1234567890123456789012345"
    barcode = head + dv11(head + rest) + rest
    b1, b2, b3 = barcode[:4] + barcode[19:24], barcode[24:34], barcode[34:44]
    return b1 + dv10(b1) + b2 + dv10(b2) + b3 + dv10(b3) + barcode[4] + barcode[5:19]


def arrec(ref):
    data = "82" + ref + "00000012345" + "12345678901234567890123456789"
    calc = dv10 if ref in "67" else lambda s: dv11(s, True)
    barcode = data[:3] + calc(data) + data[3:]
    return "".join(barcode[i : i + 11] + calc(barcode[i : i + 11]) for i in range(0, 44, 11))


def crc(body):
    prefix = body + "6304"
    return prefix + f"{binascii.crc_hqx(prefix.encode(), 0xFFFF):04X}"


@pytest.mark.parametrize(
    "fator,expected,legacy",
    [
        (1000, date(2025, 2, 22), date(2000, 7, 3)),
        (1001, date(2025, 2, 23), date(2000, 7, 4)),
        (9999, date(2049, 10, 13), date(2025, 2, 21)),
    ],
)
def test_rn09_fator_ciclos(fator, expected, legacy):
    r = ler(codigo=bancario(fator))
    assert r.vencimento == expected and r.vencimentos_possiveis == (expected, legacy)
    assert r.valor_centavos == 12345 and r.avisos


def test_rn09_aviso_fator_data_em_formato_brasileiro():
    result = ler(codigo=bancario(1000))
    assert any("03/07/2000" in aviso for aviso in result.avisos)
    assert all("2000-07-03" not in aviso for aviso in result.avisos)
    assert result.vencimentos_possiveis == (date(2025, 2, 22), date(2000, 7, 3))


def test_rn09_fator_ausente_e_legado():
    assert ler(codigo=bancario(0)).vencimentos_possiveis == ()
    assert ler(codigo=bancario(999)).vencimento == date(2000, 7, 2)


def test_rn08_bancario_formatado_e_mutacoes():
    s = bancario(1000)
    assert ler(codigo=s[:5] + "." + s[5:10] + " " + s[10:]).codigo == s
    for i in (9, 20, 31, 32):
        with pytest.raises(ErroValidacao):
            ler(codigo=s[:i] + str((int(s[i]) + 1) % 10) + s[i + 1 :])


@pytest.mark.parametrize("ref", "6789")
def test_rn10_arrecadacao_referencias(ref):
    s = arrec(ref)
    r = ler(codigo=s)
    assert r.valor_centavos == (12345 if ref in "68" else None)
    assert r.vencimento is None
    for i in (11, 23, 35, 47):
        with pytest.raises(ErroValidacao):
            ler(codigo=s[:i] + str((int(s[i]) + 1) % 10) + s[i + 1 :])
    # A forged general check digit with its block DV recalculated must still fail.
    altered = s[:3] + str((int(s[3]) + 1) % 10) + s[4:11]
    calc = dv10 if ref in "67" else lambda x: dv11(x, True)
    with pytest.raises(ErroValidacao):
        ler(codigo=altered + calc(altered) + s[12:])


def test_febraban_official_modulo_examples():
    assert _mod10("01230067896") == 3
    assert _mod11("01230067896", True) == 0


def test_rf09_bcb_vetores_oficiais():
    assert ler(codigo=STATIC).beneficiario == "Fulano de Tal"
    r = ler(codigo=DYNAMIC)
    assert r.valor_centavos is None and r.codigo == DYNAMIC and r.avisos


def test_rf09_valor_utf8_e_tlv_adversario():
    body = (
        "00020126580014br.gov.bcb.pix0136123e4567-e12b-12d1-a456-426655440"
        "0005204000053039865406100.505802BR5905José6008BRASILIA62070503***"
    )
    r = ler(codigo=crc(body))
    assert r.valor_centavos == 10050 and r.beneficiario == "José"
    for raw in [
        crc(body.replace("5905", "5904")),
        crc(body.replace("5303986", "5303840")),
        crc(body.replace("5406100.50", "54061e2.50")),
        crc(body + "5303986"),
        STATIC[:-1] + "E",
        STATIC[:-4],
    ]:
        with pytest.raises(ErroValidacao):
            ler(codigo=raw)


@pytest.mark.parametrize(
    "raw,normal",
    [
        ("529.982.247-25", "52998224725"),
        ("11.222.333/0001-81", "11222333000181"),
        ("12.ABC.345/01DE-35", "12ABC34501DE35"),
        ("USER@example.com", "user@example.com"),
        ("+5585999999999", "+5585999999999"),
        (
            "123e4567-e12b-12d1-a456-426655440000",
            "123e4567-e12b-12d1-a456-426655440000",
        ),
    ],
)
def test_rf09_chave_pix(raw, normal):
    assert ler(chave_pix=raw).chave_pix == normal


@pytest.mark.parametrize(
    "raw",
    [
        "11111111111",
        "52998224724",
        "11222333000180",
        "12ABC34501DE34",
        "a%b@example.com",
        "bad@-bad.com",
        "+0123",
        "not a key",
    ],
)
def test_rf09_chave_invalida(raw):
    with pytest.raises(ErroValidacao):
        ler(chave_pix=raw)


@pytest.mark.parametrize(
    "raw",
    [
        bancario(1000) + "a",
        bancario(1000).replace("0", "０", 1),
        bancario(1000) + "-",
        "0" * 4097,
        "",
        "1" * 46,
    ],
)
def test_rn08_codigo_invalido(raw):
    with pytest.raises(ErroValidacao):
        ler(codigo=raw)


def _campo(tag, value):
    return f"{tag}{len(value.encode('utf-8')):02d}{value}"


def _trocar_conta(payload, key, *, gui="br.gov.bcb.pix", tag="01"):
    replacement = _campo("26", _campo("00", gui) + _campo(tag, key))
    return crc(payload[:6] + replacement + payload[payload.index("52040000") : -8])


def test_rf09_dinamico_ignora_valor_sem_acesso_rede(monkeypatch):
    import socket

    def interditado(*args, **kwargs):
        raise AssertionError("A leitura não deve acessar rede")

    monkeypatch.setattr(socket, "create_connection", interditado)
    monkeypatch.setattr(socket.socket, "connect", interditado)
    payload = crc(DYNAMIC[:-8].replace("5802BR", "54041.005802BR"))
    result = ler(codigo=payload)
    assert result.valor_centavos is None
    assert result.codigo == payload
    assert any("informe valor" in aviso for aviso in result.avisos)


def test_rf09_gui_insensivel_a_caixa_e_sem_destinatario_pix_duplicado():
    upper = _trocar_conta(STATIC, "52998224725", gui="BR.GOV.BCB.PIX")
    assert ler(codigo=upper).codigo == upper
    extra = _campo("27", _campo("00", "BR.GOV.BCB.PIX") + _campo("01", "52998224725"))
    duplicate = crc(STATIC[:-8].replace("52040000", extra + "52040000"))
    with pytest.raises(ErroValidacao):
        ler(codigo=duplicate)


@pytest.mark.parametrize("chave", ["not a key", "11111111111", "52998224724"])
def test_rf09_brcode_rejeita_chave_interna_invalida(chave):
    with pytest.raises(ErroValidacao):
        ler(codigo=_trocar_conta(STATIC, chave))


@pytest.mark.parametrize("txid", ["!", "a" * 26, "**", "á"])
def test_rf09_brcode_txid_estatico_invalido(txid):
    replacement = _campo("62", _campo("05", txid))
    with pytest.raises(ErroValidacao):
        ler(codigo=crc(STATIC[:-8].replace("62070503***", replacement)))


@pytest.mark.parametrize(
    "location",
    [
        "javascript:alert(1)",
        "https://pix.example.com/id",
        "example.com",
        "example.com/a b",
        "x..com/path",
        "example.com/%GG",
        "example.com@evil.com/path",
    ],
)
def test_rf09_brcode_location_invalida(location):
    with pytest.raises(ErroValidacao):
        ler(codigo=_trocar_conta(STATIC, location, tag="25"))


@pytest.mark.parametrize("segmento", ["0", "8"])
def test_rn10_segmento_invalido(segmento):
    # Independent builder recomputes all verification digits for the invalid segment.
    data = "8" + segmento + "6" + "00000012345" + "12345678901234567890123456789"
    barra = data[:3] + dv10(data) + data[3:]
    linha = "".join(barra[i : i + 11] + dv10(barra[i : i + 11]) for i in range(0, 44, 11))
    with pytest.raises(ErroValidacao):
        ler(codigo=linha)


def test_rn10_vetor_segmento_zero_fornecido_na_revisao():
    with pytest.raises(ErroValidacao):
        ler(codigo="806000000018234512345674890123456786901234567898")


@pytest.mark.parametrize("chave", ["529.982.247-25", " 52998224725 ", "USER@example.com"])
def test_rf09_brcode_rejeita_chave_nao_canonica(chave):
    with pytest.raises(ErroValidacao):
        ler(codigo=_trocar_conta(STATIC, chave))


@pytest.mark.parametrize(
    "chave",
    [
        "52998224725",
        "user@example.com",
        "+5585999999999",
        "12ABC34501DE35",
        "123e4567-e12b-12d1-a456-426655440000",
    ],
)
def test_rf09_brcode_preserva_chave_canonica(chave):
    payload = _trocar_conta(STATIC, chave)
    assert ler(codigo=payload).codigo == payload


@pytest.mark.parametrize("valor", ["0", "0.0", "0.00", "000.00"])
def test_rf09_brcode_estatico_valor_zero_invalido(valor):
    payload = crc(STATIC[:-8].replace("5802BR", _campo("54", valor) + "5802BR"))
    with pytest.raises(ErroValidacao):
        ler(codigo=payload)


def test_rf09_brcode_dinamico_ignora_valor_zero():
    payload = crc(DYNAMIC[:-8].replace("5802BR", "54040.005802BR"))
    assert ler(codigo=payload).valor_centavos is None
