"""Pagos que se repiten y aumentos."""
import recurrentes as rc


def mov(fecha, desc, monto, cat="Servicios", moneda="ARS", ent="Banco"):
    return {"fecha": fecha, "descripcion": desc, "monto": monto, "moneda": moneda, "categoria": cat, "entidad": ent}


def test_detecta_fijos_y_aumentos():
    ms = [
        mov("2026-09-03", "NETFLIX 123456789", -11999, "Suscripciones"), mov("2026-10-03", "Netflix 987654321", -11999, "Suscripciones"),
        mov("2026-11-03", "Netflix", -14999, "Suscripciones"),
        mov("2026-09-12", "Edenor", -38000), mov("2026-10-12", "Edenor", -40000),
        # súper: varias compras por mes -> no es un pago fijo
        mov("2026-09-05", "Coto", -20000, "Supermercado"), mov("2026-09-20", "Coto", -30000, "Supermercado"),
        mov("2026-10-07", "Coto", -25000, "Supermercado"), mov("2026-10-21", "Coto", -24000, "Supermercado"),
        # montos muy distintos -> no
        mov("2026-09-01", "Ferretería", -5000, "Hogar"), mov("2026-10-01", "Ferretería", -60000, "Hogar"),
        # un solo mes y no es suscripción -> no
        mov("2026-11-01", "Gimnasio", -30000, "Salud"),
        # suscripción nueva de un solo mes -> sí
        mov("2026-11-08", "Disney+", -8999, "Suscripciones"),
        # excluidos: ingresos, entre mis cuentas, pago de tarjeta
        mov("2026-09-01", "Sueldo", 900000, "Sueldo"), mov("2026-10-01", "Sueldo", 900000, "Sueldo"),
        mov("2026-09-10", "A mi cuenta", -100000, "Entre mis cuentas"), mov("2026-10-10", "A mi cuenta", -100000, "Entre mis cuentas"),
        mov("2026-09-15", "Pago Visa", -200000, "Pago de tarjeta"), mov("2026-10-15", "Pago Visa", -200000, "Pago de tarjeta"),
    ]
    r = rc.detectar(ms, excluidas={"Entre mis cuentas"})
    pagos = {p["descripcion"]: p for p in r["pagos"]}
    assert set(pagos) == {"Netflix", "Edenor", "Disney+"}
    n = pagos["Netflix"]
    assert n["meses"] == 3 and n["mensual"] == 14999 and n["anual"] == 14999 * 12
    assert n["aumento"] == {"anterior": 11999, "actual": 14999, "pct": 25.0, "mes": "2026-11"}
    assert pagos["Edenor"]["aumento"]["pct"] == 5.3      # +$2.000 y +5,3%: alcanza los dos mínimos
    assert r["aumentos"] == 2 and r["total_mensual"] == 14999 + 40000 + 8999


def test_umbral_de_aumento():
    base = [mov("2026-09-01", "Luz", -10000), mov("2026-10-01", "Luz", -10400)]     # +4%: no
    assert rc.detectar(base)["pagos"][0]["aumento"] is None
    chico = [mov("2026-09-01", "App", -1000), mov("2026-10-01", "App", -1200)]       # +20% pero $200: no
    assert rc.detectar(chico)["pagos"][0]["aumento"] is None
    grande = [mov("2026-09-01", "Prepaga", -100000), mov("2026-10-01", "Prepaga", -108000)]
    assert rc.detectar(grande)["pagos"][0]["aumento"]["pct"] == 8.0


def test_dolares():
    ms = [mov("2026-09-01", "iCloud", -2.99, "Suscripciones", "USD"), mov("2026-10-01", "iCloud", -2.99, "Suscripciones", "USD")]
    assert rc.detectar(ms)["pagos"] == []                       # sin dólar no se puede pasar a pesos
    assert rc.detectar(ms, tipo_cambio=1000)["pagos"][0]["mensual"] == 2990


def test_avisos():
    ms = [mov("2026-09-01", "Netflix", -10000, "Suscripciones"), mov("2026-10-01", "Netflix", -12500, "Suscripciones"),
          mov("2026-09-02", "Spotify", -5000, "Suscripciones"), mov("2026-10-02", "Spotify", -5500, "Suscripciones")]
    av = rc.avisos(rc.detectar(ms))
    assert [a["titulo"] for a in av] == ["Netflix subió 25%", "Spotify subió 10%"]
    assert av[0]["nivel"] == "media" and av[1]["nivel"] == "baja"
    assert av[0]["detalle"] == "De $10.000 a $12.500 por mes ($30.000 más por año)."
