import tomllib

import configuracion


def test_ida_y_vuelta_con_claves_raras(carpeta):
    cfg = configuracion.cargar()
    cfg["presupuestos"] = {"total": 900000, "categorias": {"Delivery y restaurantes": 50000, "Educación": 1}}
    cfg["categorias"]["reglas"] = {'transferencia "rara" s a': "Servicios"}
    configuracion.guardar(cfg)
    leido = tomllib.load(open("config.toml", "rb"))
    assert leido["presupuestos"]["categorias"]["Delivery y restaurantes"] == 50000
    assert configuracion.cargar() == cfg


def test_migracion_de_version_anterior(carpeta):
    open("config.toml", "w").write('[fuentes]\niol = true\n[analisis]\nactivado = false\nmodelo = "sonnet"\n')
    cfg = configuracion.cargar()
    assert cfg["brokers"]["iol"]["activo"] is True and "iol" not in cfg["fuentes"]
    assert cfg["analisis"]["claude_code"]["modelo"] == "sonnet" and "modelo" not in cfg["analisis"]


def test_llavero_migra_nombre_anterior(llavero):
    llavero.set_password("wallet-dashboard", "github_token", "tok")
    assert configuracion.leer_secreto("github_token") == "tok"
    assert ("pluto", "github_token") in llavero.d and ("wallet-dashboard", "github_token") not in llavero.d
