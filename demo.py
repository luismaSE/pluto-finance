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
        "titular": "Buen patrimonio, pero $4 M en pesos pierden contra la inflación",
        "salud": {"puntaje": 68, "etiqueta": "Bien"},
        "indicadores": [{"nombre": "Liquidez ociosa", "estado": "mal", "valor": "$4 M"},
                        {"nombre": "Diversificación", "estado": "regular", "valor": "GGAL 34%"},
                        {"nombre": "Ahorro del mes", "estado": "bien", "valor": "22%"},
                        {"nombre": "Exposición al dólar", "estado": "regular", "valor": "30%"}],
        "resumen": "Patrimonio diversificado con buen rendimiento en renta variable, pero con unos $4 M en pesos sin rendimiento claro y una concentración alta en GGAL.",
        "observaciones": ["70% del patrimonio está en pesos", "Suscripciones: $25.000 por mes", "Gastos estables contra el mes pasado"],
        "alertas": [{"nivel": "alta", "titulo": "Pesos parados en caja de ahorro", "detalle": "$2,8 M en la caja de ahorro de Galicia no generan interés."},
                    {"nivel": "media", "titulo": "Concentración en GGAL", "detalle": "GGAL representa ~34% de la cartera de inversiones."},
                    {"nivel": "baja", "titulo": "Comisión de mantenimiento", "detalle": "Se cobra comisión de mantenimiento; revisá si tu paquete la bonifica."}],
        "recomendaciones": [{"titulo": "Pasar liquidez a un money market", "detalle": "Dejá en caja de ahorro lo del mes y el resto en un FCI de liquidez inmediata.", "impacto": "alto", "ahorro_mensual_ars": 62_000},
                            {"titulo": "Bajar GGAL a menos del 20%", "detalle": "Repartí la diferencia entre bonos en dólares y CEDEARs.", "impacto": "medio", "ahorro_mensual_ars": 0},
                            {"titulo": "Revisar suscripciones", "detalle": "Tres servicios de streaming suman $25.000 por mes.", "impacto": "bajo", "ahorro_mensual_ars": 9_000}],
    }
    return s


def precios_demo() -> dict:
    """Precios ficticios (caminata aleatoria de un año) para la pestaña Mercado."""
    from datetime import timedelta
    rnd = random.Random(11)
    hoy = date.today()
    base = {"GGAL": (6900, 0.0012, 0.028), "AL30": (827, 0.0005, 0.012), "SPY": (26250, 0.0009, 0.011),
            "MELI": (29140, 0.0002, 0.024), "YPFD": (49000, 0.0014, 0.026), "PAMP": (3900, 0.0008, 0.022)}
    out = {}
    for sim, (final, deriva, vol) in base.items():
        dias = [hoy - timedelta(days=d) for d in range(400, -1, -1) if (hoy - timedelta(days=d)).weekday() < 5]
        p, serie = 1.0, []
        for d in dias:
            p *= 1 + rnd.gauss(deriva, vol)
            serie.append([d.isoformat(), p])
        k = final / serie[-1][1]
        serie = [[f, round(v * k, 2)] for f, v in serie]
        out[sim] = {"mercado": "bCBA", "precio": serie[-1][1], "moneda": "ARS", "fecha": serie[-1][0],
                    "variacion_dia": round((serie[-1][1] / serie[-2][1] - 1) * 100, 2), "serie": serie}
    return out


def registro_demo(precios: dict) -> list:
    """Recomendaciones ficticias de análisis anteriores, para ver el seguimiento."""
    from datetime import timedelta
    def hace(dias, sim):
        f = (date.today() - timedelta(days=dias)).isoformat()
        serie = precios[sim]["serie"]
        return f, next((p for d, p in reversed(serie) if d <= f), serie[0][1])
    out = []
    for dias, acc, sim, por, conf in ((75, "reducir", "GGAL", "", "media"), (75, "comprar", "SPY", "", "alta"),
                                      (40, "cambiar", "MELI", "PAMP", "baja"), (12, "aumentar", "AL30", "", "media")):
        f, p = hace(dias, sim)
        out.append({"fecha": f + "T10:00", "accion": acc, "activo": sim, "por": por, "confianza": conf,
                    "motivo": "Recomendación de ejemplo.", "precio": p,
                    "precio_por": hace(dias, por)[1] if por else None})
    return out


def analisis_mercado_demo() -> dict:
    return {
        "titular": "Demasiado GGAL: sumá renta fija en dólares",
        "puntos_clave": ["GGAL pesa 34% de tus inversiones", "Poca renta fija para un perfil moderado", "CEDEARs te cubren de una suba del CCL"],
        "termometro": {"riesgo_cartera": 4, "riesgo_perfil": 3, "diversificacion": 2, "sentimiento": "neutral"},
        "resumen": "Datos ficticios. El mercado local viene con volatilidad alta por la incertidumbre cambiaria. "
                   "Tu cartera está cargada en acciones bancarias argentinas y tiene poca renta fija en dólares para un perfil moderado.",
        "cartera_objetivo": [
            {"clase": "Acciones argentinas", "actual_pct": 44, "objetivo_pct": 25, "comentario": "Alta concentración en GGAL."},
            {"clase": "CEDEARs", "actual_pct": 23, "objetivo_pct": 25, "comentario": "Diversifican y siguen al CCL."},
            {"clase": "Renta fija en dólares", "actual_pct": 13, "objetivo_pct": 25, "comentario": "Bonos soberanos y ONs cortas."},
            {"clase": "Liquidez y money market", "actual_pct": 20, "objetivo_pct": 25, "comentario": "Fondo de emergencia de 6 meses."},
        ],
        "recomendaciones": [
            {"accion": "reducir", "activo": "GGAL", "por": "", "titulo": "Bajar la concentración en un banco", "monto_ars": 2_500_000, "horizonte": "mediano", "confianza": "media",
             "motivo": "Pesa más del 30% de tus inversiones: un mal balance del banco golpea toda la cartera.",
             "riesgos": "Si el sector financiero sigue subiendo, te perdés parte de esa suba."},
            {"accion": "aumentar", "activo": "AL30", "por": "", "titulo": "Sumar renta fija en dólares", "monto_ars": 1_500_000, "horizonte": "largo", "confianza": "media",
             "motivo": "Suma renta fija en dólares acorde a tu perfil.", "riesgos": "Riesgo soberano: el precio cae si sube el riesgo país."},
            {"accion": "cambiar", "activo": "MELI", "por": "SPY", "titulo": "Diversificar con el S&P 500", "monto_ars": 1_000_000, "horizonte": "largo", "confianza": "baja",
             "motivo": "SPY diversifica entre 500 empresas con menos volatilidad.", "riesgos": "Menor potencial de suba que una acción individual."},
        ],
        "noticias": [
            {"titulo": "Noticia de ejemplo sobre resultados de bancos", "fuente": "Demo", "fecha": date.today().isoformat(),
             "activos": ["GGAL"], "impacto": "incierto", "que_significa": "Las noticias reales aparecen si el proveedor de IA puede buscar en la web."},
            {"titulo": "Noticia de ejemplo: baja el riesgo país", "fuente": "Demo", "fecha": date.today().isoformat(),
             "activos": ["AL30", "GGAL"], "impacto": "positivo", "que_significa": "Favorece a bonos y bancos."},
        ],
        "escenarios": [
            {"escenario": "Si el dólar CCL sube 15%", "probabilidad": "media", "efecto": "mixto", "detalle": "Tus CEDEARs suben en pesos; las acciones locales dependen del contexto.",
             "que_considerar": "Tener parte de la cartera dolarizada amortigua el golpe."},
            {"escenario": "Si baja el riesgo país", "probabilidad": "media", "efecto": "positivo", "detalle": "Suben los bonos soberanos y las acciones bancarias.",
             "que_considerar": "Es el escenario que más favorece a tu cartera actual."},
            {"escenario": "Si se endurece el cepo", "probabilidad": "baja", "efecto": "negativo", "detalle": "Caen las acciones locales y se amplía la brecha.",
             "que_considerar": "La liquidez en dólares te da margen."},
        ],
        "proveedor": "demo", "modelo": "", "con_noticias": False, "fecha": date.today().isoformat() + "T10:00",
    }
