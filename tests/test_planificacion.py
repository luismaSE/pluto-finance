from datetime import date

import avisos
import presupuestos
import tarjetas


def test_proxima_fecha():
    assert tarjetas.proxima_fecha(10, date(2026, 11, 5)) == date(2026, 11, 10)
    assert tarjetas.proxima_fecha(5, date(2026, 11, 5)) == date(2026, 11, 5)       # hoy cuenta
    assert tarjetas.proxima_fecha(3, date(2026, 12, 20)) == date(2027, 1, 3)       # cambio de año
    assert tarjetas.proxima_fecha(31, date(2026, 2, 10)) == date(2026, 2, 28)      # mes corto


def test_tarjetas_fecha_exacta_y_ultimo_pago():
    t = tarjetas.calcular({"v": {"nombre": "Visa", "cierre": 24, "vencimiento": 7, "proximo_vencimiento": "2026-11-09"}},
                          date(2026, 11, 5), [{"descripcion": "PAGO TARJETA VISA", "monto": -1000, "fecha": "2026-10-07", "moneda": "ARS"},
                                              {"descripcion": "PAGO TARJETA MASTER", "monto": -500, "fecha": "2026-10-20", "moneda": "ARS"}])[0]
    assert t["dias_vencimiento"] == 4 and t["dias_cierre"] == 19
    assert t["ultimo_pago"]["monto"] == 1000                                         # solo los pagos de esa marca
    vieja = tarjetas.calcular({"v": {"nombre": "Visa", "vencimiento": 7, "proximo_vencimiento": "2026-10-01"}}, date(2026, 11, 5))[0]
    assert vieja["proximo_vencimiento"] == "2026-11-07"                              # una fecha exacta pasada se ignora


def test_presupuestos_estado_y_proyeccion():
    g = {"2026-11": {"total_ars": 500_000, "por_categoria": {"Supermercado": 290_000, "Delivery y restaurantes": 70_000}}}
    p = presupuestos.evaluar({"total": 1_000_000, "categorias": {"Supermercado": 300_000, "Delivery y restaurantes": 50_000}}, g, date(2026, 11, 15))
    m = p["meses"]["2026-11"]
    assert m["total"]["estado"] == "ok" and m["total"]["proyeccion"] == 1_000_000
    estados = {c["nombre"]: c["estado"] for c in m["categorias"]}
    assert estados == {"Supermercado": "cerca", "Delivery y restaurantes": "excedido"}
    # antes del día 7 no se proyecta
    assert presupuestos.evaluar({"total": 1}, g, date(2026, 11, 3))["meses"]["2026-11"]["total"]["proyeccion"] is None
    assert presupuestos.evaluar({}, g)["configurado"] is False


def test_avisos():
    hoy = date(2026, 11, 5)
    t = tarjetas.calcular({"v": {"nombre": "Visa", "vencimiento": 6, "cierre": 6}}, hoy)
    g = {"2026-11": {"total_ars": 0, "por_categoria": {"Supermercado": 400_000}}}
    p = presupuestos.evaluar({"categorias": {"Supermercado": 300_000}}, g, hoy)
    a = avisos.generar({"liquidez": [{"entidad": "Banco X", "al": "2026-09-01"}]}, t, p, hoy)
    titulos = [x["titulo"] for x in a]
    assert titulos[0] in ("Visa vence mañana", "Te pasaste del límite: Supermercado")   # primero los urgentes
    assert "Visa cierra mañana" in titulos and "Resumen de Banco X desactualizado" in titulos
    assert [x["nivel"] for x in a] == sorted([x["nivel"] for x in a], key=["alta", "media", "baja"].index)
