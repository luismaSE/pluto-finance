"""Datos ficticios para probar el dashboard sin loguearse."""
import random
from datetime import date

from modelo import Snapshot, Cuenta, Movimiento, Inversion


def snapshot_demo() -> Snapshot:
    random.seed(7)
    hoy = date.today()
    s = Snapshot()
    s.cotizaciones = {"oficial": {"compra": 1415, "venta": 1465}, "mep": {"compra": 1478, "venta": 1489},
                      "ccl": {"compra": 1495, "venta": 1503}, "blue": {"compra": 1460, "venta": 1480}}
    s.cuentas = [
        Cuenta("Galicia", "Caja de ahorro en pesos", "ARS", 2_845_300.55),
        Cuenta("Galicia", "Caja de ahorro en dólares", "USD", 4_350.00),
        Cuenta("Mercado Pago", "Dinero disponible", "ARS", 1_120_480.10),
        Cuenta("IOL", "Disponible para operar (Argentina)", "ARS", 410_250.00),
        Cuenta("IOL", "Disponible para operar (Argentina)", "USD", 312.40),
    ]
    s.inversiones = [
        Inversion("IOL", "GGAL", "Grupo Financiero Galicia", "ACCIONES", 900, 6_210_000, "ARS", 1.8, 22.4, 1_136_000),
        Inversion("IOL", "AL30", "Bono Rep. Argentina 2030", "TITULOSPUBLICOS", 3000, 2_480_000, "ARS", -0.4, 9.1, 207_000),
        Inversion("IOL", "SPY", "CEDEAR SPDR S&P 500", "CEDEARS", 120, 3_150_000, "ARS", 0.6, 31.7, 758_000),
        Inversion("IOL", "MELI", "CEDEAR MercadoLibre", "CEDEARS", 35, 1_020_000, "ARS", -2.1, -4.3, -46_000),
        Inversion("IOL", "YPFD", "YPF S.A.", "ACCIONES", 40, 1_960_000, "ARS", 2.9, 41.0, 570_000),
        Inversion("Galicia", "Fima Premium", "FCI Money Market", "FCI", 0, 1_800_000, "ARS"),
        Inversion("Galicia", "Plazo fijo 30d", "Plazo fijo tradicional", "PLAZO FIJO", 0, 1_500_000, "ARS"),
    ]
    comercios = [("Coto", 18000, 65000), ("Carrefour", 12000, 48000), ("Rappi", 6000, 22000), ("PedidosYa", 7000, 25000),
                 ("YPF", 25000, 55000), ("Uber", 3500, 12000), ("Netflix", 11999, 11999), ("Spotify", 4199, 4199),
                 ("Disney+", 8999, 8999), ("Edenor", 38000, 38000), ("Personal", 21000, 21000),
                 ("Farmacity", 8000, 30000), ("MercadoLibre", 15000, 120000), ("Café Martínez", 4500, 9000),
                 ("Comisión mantenimiento de cuenta", 9800, 9800), ("Percepción IVA RG 4240", 6200, 6200)]
    for _ in range(46):
        c, lo, hi = random.choice(comercios)
        dia = random.randint(1, hoy.day)
        ent = random.choice(["Galicia", "Galicia", "Mercado Pago"])
        s.movimientos.append(Movimiento(hoy.replace(day=dia).isoformat(), ent, c, -round(random.uniform(lo, hi), 2), "ARS"))
    s.movimientos.append(Movimiento(hoy.replace(day=1).isoformat(), "Galicia", "Acreditación de haberes", 3_400_000, "ARS"))
    ini, hoy_iso = hoy.replace(day=1).isoformat(), hoy.isoformat()
    for c in s.cuentas + s.inversiones:
        c.al = hoy_iso
    s.cobertura = [{"entidad": "Galicia", "cuenta": "Caja de ahorro en pesos", "desde": ini, "hasta": hoy_iso},
                   {"entidad": "Mercado Pago", "cuenta": "Dinero en cuenta", "desde": ini, "hasta": hoy_iso}]
    s.estado_fuentes = {"IOL": {"ok": True, "detalle": "API oficial"},
                        "Mercado Pago": {"ok": True, "detalle": "PDF (demo)"},
                        "Galicia": {"ok": True, "detalle": "PDF (demo)"}}
    s.advertencias = ["Datos ficticios de demostración."]
    s.analisis = {
        "resumen": "Patrimonio diversificado con buen rendimiento en renta variable, pero con unos $4 M en pesos sin rendimiento claro y una concentración alta en GGAL.",
        "observaciones": ["El 70% del patrimonio está en pesos o en activos que cotizan en pesos.",
                          "Las suscripciones suman cerca de $25.000 por mes."],
        "alertas": [{"nivel": "alta", "titulo": "Pesos parados en caja de ahorro", "detalle": "$2,8 M en la caja de ahorro de Galicia no generan interés."},
                    {"nivel": "media", "titulo": "Concentración en GGAL", "detalle": "GGAL representa ~34% de la cartera de inversiones."},
                    {"nivel": "baja", "titulo": "Comisión de mantenimiento", "detalle": "Se cobra comisión de mantenimiento; revisá si tu paquete la bonifica."}],
        "recomendaciones": [{"titulo": "Mover liquidez a un FCI money market", "detalle": "Dejá en caja de ahorro lo necesario para el mes y el resto en un FCI de liquidez inmediata.", "impacto": "alto"},
                            {"titulo": "Rebalancear la cartera", "detalle": "Llevar GGAL a menos del 20% de la cartera.", "impacto": "medio"}],
    }
    return s
