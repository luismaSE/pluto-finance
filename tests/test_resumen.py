from datetime import date

import resumen
from modelo import Cuenta, Inversion, Movimiento, Snapshot


def test_gastos_por_mes_excluye_movimientos_propios():
    s = Snapshot()
    s.cotizaciones = {"mep": {"venta": 1000}}
    s.cuentas = [Cuenta("Banco", "Caja de ahorro", "ARS", 100_000, "2026-10-31"), Cuenta("Banco", "Caja USD", "USD", 100, "2026-10-31")]
    s.inversiones = [Inversion("Broker", "AAA", "Acción", "ACCIONES", 1, 50_000, "ARS")]
    s.movimientos = [
        Movimiento("2026-10-02", "Banco", "Super", -10_000, "ARS", "Supermercado"),
        Movimiento("2026-10-03", "Banco", "A mi otra cuenta", -40_000, "ARS", "Entre mis cuentas"),
        Movimiento("2026-10-05", "Banco", "Sueldo", 200_000, "ARS", "Sueldo"),
        Movimiento("2026-10-06", "Banco", "Compra en dólares", -10, "USD", "Compras online"),
    ]
    r = resumen.calcular(s)
    assert r["patrimonio_ars"] == 100_000 + 100_000 + 50_000
    g = r["gastos_por_mes"]["2026-10"]
    assert g["total_ars"] == 10_000 + 10 * 1000          # sin la transferencia propia, USD a MEP
    assert g["ingresos_ars"] == 200_000
    assert g["por_categoria"]["Supermercado"] == 10_000
