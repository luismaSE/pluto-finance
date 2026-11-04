"""Compatibilidad: el análisis ahora vive en el paquete ia/ (varios proveedores)."""
import configuracion
import ia


def analizar(resumen: dict, cotizaciones: dict, modelo: str | None = None, referencias: dict | None = None) -> dict:
    cfg = configuracion.cargar()["analisis"]
    if modelo:
        cfg = {**cfg, "modelo": modelo}
    return ia.analizar(resumen, cotizaciones, cfg, configuracion.leer_secreto, referencias)


if __name__ == "__main__":
    # Prueba rápida del proveedor configurado: python analisis.py
    print(ia.probar(configuracion.cargar()["analisis"], configuracion.leer_secreto))
