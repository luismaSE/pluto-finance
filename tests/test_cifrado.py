import pytest
from cryptography.exceptions import InvalidTag

import cifrado


def test_ida_y_vuelta_con_acentos():
    datos = {"texto": "ñandú €", "n": [1, 2, 3]}
    sobre = cifrado.cifrar(datos, "una frase larga con ñ")
    assert cifrado.descifrar(sobre, "una frase larga con ñ") == datos


def test_contrasena_incorrecta():
    sobre = cifrado.cifrar({"a": 1}, "una frase larga correcta")
    with pytest.raises(InvalidTag):
        cifrado.descifrar(sobre, "otra frase distinta")


def test_archivo_modificado_se_rechaza():
    import base64, json
    sobre = json.loads(cifrado.cifrar({"a": 1}, "una frase larga correcta"))
    ct = bytearray(base64.b64decode(sobre["ct"])); ct[0] ^= 1
    sobre["ct"] = base64.b64encode(bytes(ct)).decode()
    with pytest.raises(InvalidTag):
        cifrado.descifrar(json.dumps(sobre).encode(), "una frase larga correcta")
