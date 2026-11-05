import pytest
import requests

from utils import fecha_iso, mensaje_error, normalizar_moneda, parse_monto


@pytest.mark.parametrize("texto,esperado", [
    ("$ 1.234,56", 1234.56), ("-1,234.56", -1234.56), ("U$S 10", 10.0), ("1.234", 1234.0),
    ("12,5", 12.5), ("(500,00)", -500.0), (42, 42.0), ("", None), (None, None), ("abc", None),
])
def test_parse_monto(texto, esperado):
    assert parse_monto(texto) == esperado


@pytest.mark.parametrize("v,esperado", [("peso_Argentino", "ARS"), ("$", "ARS"), ("USD", "USD"),
                                        ("dolar_Estadounidense", "USD"), ("U$S", "USD"), ("xyz", None)])
def test_normalizar_moneda(v, esperado):
    assert normalizar_moneda(v) == esperado


def test_fecha_iso():
    assert fecha_iso("2026-11-03T10:00:00") == "2026-11-03"
    assert fecha_iso("03/11/26") == "2026-11-03"
    assert fecha_iso("3-11-2026") == "2026-11-03"
    assert fecha_iso("cualquier cosa") is None


def test_mensajes_de_error():
    assert "conexión" in mensaje_error(requests.exceptions.ConnectionError("pool"), "IOL")
    assert "tardó" in mensaje_error(requests.exceptions.Timeout(), "IOL")
    r = requests.Response(); r.status_code = 401
    assert "rechazó el acceso" in mensaje_error(requests.exceptions.HTTPError(response=r), "GitHub")
    assert mensaje_error(RuntimeError("Clave inválida"), "X") == "Clave inválida"
