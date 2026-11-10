"""La respuesta de la IA se revisa antes de mostrarla: rangos, listas y valores válidos."""
from ia import normalizar as n


def test_numeros_en_formatos_comunes():
    assert n.numero("1.500.000") == 1500000
    assert n.numero("$ 2,5") == 2.5
    assert n.numero("1.500.000,50") == 1500000.5
    assert n.numero("38%") == 38
    assert n.numero(7, 1, 5) == 5 and n.numero(-3, 0) == 0
    assert n.numero("sin dato") is None and n.numero(True) is None and n.numero(float("nan")) is None


def test_mercado_fuera_de_rango_y_basura():
    a = n.mercado({
        "titular": "x" * 500,
        "puntos_clave": ["uno", "", "dos", "tres", "cuatro"],
        "termometro": {"riesgo_cartera": 9, "riesgo_perfil": "3", "diversificacion": 0, "sentimiento": "Eufórico"},
        "cartera_objetivo": [{"clase": "CEDEARs", "actual_pct": "23%", "objetivo_pct": 140}, "basura"],
        "recomendaciones": [
            {"accion": "Comprar", "activo": "SPY", "monto_ars": "1.000.000", "confianza": "ALTA", "por": "AL30"},
            {"accion": "operar ya", "activo": "GGAL"},           # acción inválida: se descarta
            {"accion": "vender"},                               # sin activo: se descarta
            {"accion": "cambiar", "activo": "MELI", "por": "SPY", "confianza": "mucha"},
            {"accion": "reducir", "activo": "A"}, {"accion": "reducir", "activo": "B"}, {"accion": "reducir", "activo": "C"},
        ],
        "noticias": [{"titulo": "N", "fecha": "ayer", "impacto": "bueno", "activos": "GGAL"}] * 9,
        "escenarios": [{"escenario": "Si sube el dólar", "efecto": "Suben los CEDEARs en pesos"}],
    })
    assert len(a["titular"]) == 120 and a["titular"].endswith("…")
    assert a["puntos_clave"] == ["uno", "dos", "tres"]         # sin vacíos y máximo 3
    assert a["termometro"] == {"riesgo_cartera": 5, "riesgo_perfil": 3, "diversificacion": 1}
    assert a["cartera_objetivo"] == [{"clase": "CEDEARs", "actual_pct": 23, "objetivo_pct": 100, "comentario": ""}]
    r = a["recomendaciones"]
    assert [x["activo"] for x in r] == ["SPY", "MELI", "A", "B"]   # inválidas fuera, máximo 4
    assert r[0]["accion"] == "comprar" and r[0]["monto_ars"] == 1000000 and r[0]["por"] == ""   # "por" solo en cambiar
    assert r[0]["confianza"] == "alta" and r[1]["confianza"] == "baja" and r[1]["por"] == "SPY"
    assert len(a["noticias"]) == 5
    assert a["noticias"][0] | {} == {"titulo": "N", "fuente": "", "fecha": "", "activos": ["GGAL"], "impacto": "incierto", "que_significa": ""}
    e = a["escenarios"][0]
    assert e["efecto"] == "mixto" and e["detalle"] == "Suben los CEDEARs en pesos"   # formato anterior


def test_general():
    a = n.general({"resumen": "ok", "salud": {"puntaje": "140"}, "indicadores": [{"nombre": "Liquidez", "estado": "pésimo"}],
                   "alertas": [{"titulo": "A", "nivel": "urgente"}, {"detalle": "sin título"}],
                   "recomendaciones": [{"titulo": "R", "impacto": "Alto", "ahorro_mensual_ars": "-5"}], "proveedor": "P"})
    assert a["salud"]["puntaje"] == 100 and a["indicadores"][0]["estado"] == "regular"
    assert a["alertas"] == [{"nivel": "media", "titulo": "A", "detalle": ""}]
    assert a["recomendaciones"][0]["impacto"] == "alto" and a["recomendaciones"][0]["ahorro_mensual_ars"] == 0
    assert a["proveedor"] == "P" and "titular" not in a


def test_respuesta_que_no_es_json():
    import ia
    a = n.general(ia.a_json("El modelo respondió texto suelto"))
    assert a["resumen"] == "El modelo respondió texto suelto" and a["alertas"] == [] and a["recomendaciones"] == []


def test_demo_pasa_sin_cambios():
    import demo
    d = demo.analisis_mercado_demo()
    a = n.mercado(d)
    assert [r["activo"] for r in a["recomendaciones"]] == [r["activo"] for r in d["recomendaciones"]]
    assert a["termometro"] == d["termometro"] and len(a["escenarios"]) == 3
