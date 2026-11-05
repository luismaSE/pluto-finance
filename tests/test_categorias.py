from categorias import CATEGORIAS, categorizar, clave_regla


def test_palabras_clave():
    assert categorizar("Pago PedidosYa Plus") == "Delivery y restaurantes"
    assert categorizar("PAGO TARJETA VISA") == "Pago de tarjeta"
    assert categorizar("Transferencia enviada Pablo Ramirez") == "Transferencias"   # "abl" no es ABL
    assert categorizar("ABL CABA") == "Servicios"


def test_titular_es_entre_mis_cuentas():
    assert categorizar("Transferencia recibida JUAN PEREZ", ["Juan Perez"]) == "Entre mis cuentas"


def test_reglas_del_usuario_ganan():
    reglas = {clave_regla("Transferencia enviada Verduleria Don Pepe"): "Supermercado"}
    assert categorizar("Transferencia enviada Verduleria Don Pepe", (), reglas) == "Supermercado"
    # tolera puntuación y números de operación distintos
    assert categorizar("TRANSFERENCIA ENVIADA VERDULERIA DON PEPE 123456", (), reglas) == "Supermercado"


def test_clave_regla_normaliza():
    assert clave_regla("Comercio Uno S. A. S. 1234567") == "comercio uno s a s"
    assert "Otros" in CATEGORIAS
