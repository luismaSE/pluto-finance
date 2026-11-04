"""Categorización simple por palabras clave. Ajustá las reglas a tus consumos."""
import re

from utils import sin_acentos

# Movimientos que no son gasto ni ingreso real: no se suman en los totales.
EXCLUIDAS = {"Entre mis cuentas"}

# Se evalúan en orden: lo específico primero.
REGLAS = {
    "Entre mis cuentas": ["ingreso de dinero", "debito debin recurrente", "debin recurrente"],
    "Pago de tarjeta": ["pago tarjeta", "pago de resumen tarjeta", "pago resumen tarjeta"],
    "Sueldo": ["haberes", "sueldo"],
    "Rendimientos": ["rendimiento", "interes capitalizado", "intereses"],
    "Supermercado": ["verduleria", "market", "autoservicio", "kiosco", "almacen", "carniceria", "dietetica", "fiambreria", "coto", "carrefour", "jumbo", "dia ", "disco", "vea", "changomas", "chango mas", "supermerc", "walmart", "la anonima", "maxiconsumo", "vital"],
    "Delivery y restaurantes": ["rappi", "pedidosya", "pedidos ya", "mcdonald", "burger", "restaurant", "resto", "cafe", "starbucks", "havanna", "mostaza", "parrilla", "bar "],
    "Transporte": ["uber", "cabify", "didi", "sube", "ypf", "shell", "axion", "puma", "peaje", "autopista", "estacionamiento", "aerolineas", "flybondi", "jetsmart"],
    "Servicios": ["edenor", "edesur", "metrogas", "naturgy", "aysa", "telecom", "personal", "movistar", "claro", "fibertel", "telecentro", "abl", "arba", "agip", "expensas"],
    "Suscripciones": ["netflix", "spotify", "ebanx", "disney", "hbo", "max ", "amazon prime", "prime video", "youtube", "apple.com", "icloud", "google", "chatgpt", "openai", "anthropic", "claude", "paramount", "star+"],
    "Salud": ["farmacia", "farmacity", "osde", "swiss medical", "galeno", "medife", "omint", "hospital", "clinica", "odontolog"],
    "Compras online": ["mercadolibre", "mercado libre", "amazon", "aliexpress", "shein", "temu", "tiendanube"],
    "Transferencias": ["transferencia", "transf", "envio de dinero", "cvu", "cbu"],
    "Impuestos y comisiones": ["impuesto", "iva ", "percepcion", "comision", "sellos", "mantenimiento", "ganancias", "bienes personales"],
    "Educación": ["colegio", "universidad", "curso", "udemy", "coursera", "platzi"],
    "Ropa": ["zara", "adidas", "nike", "dexter", "grimoldi", "falabella", "h&m"],
}


def _norm(s):
    return " " + " ".join(sin_acentos(s or "").lower().replace(",", " ").split()) + " "


def categorizar(descripcion: str, titulares=()) -> str:
    d = _norm(descripcion)
    for t in titulares:
        if t and _norm(t).strip() in d:
            return "Entre mis cuentas"
    for cat, claves in REGLAS.items():
        # la palabra clave tiene que empezar una palabra ("abl" no matchea "pablo")
        if any(re.search(r"(?<![a-z0-9])" + re.escape(c), d) for c in claves):
            return cat
    return "Otros"
