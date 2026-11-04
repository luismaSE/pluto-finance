"""Cifrado del archivo que viaja al celular.

Formato (JSON): {"v":1, "kdf":"pbkdf2-sha256", "iter":N, "salt":b64, "iv":b64, "ct":b64}
- La clave AES-256 se deriva de tu contraseña con PBKDF2-HMAC-SHA256 (600.000 iteraciones).
- AES-256-GCM cifra y autentica: si alguien modifica el archivo, no se puede descifrar.
- El contenido es el JSON del dashboard comprimido con gzip.
La app Android implementa exactamente lo mismo (android/.../Cripto.kt).
"""
import base64
import getpass
import gzip
import json
import os

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITERACIONES = 600_000
LARGO_MINIMO = 12


def _clave(password: str, salt: bytes, iteraciones: int) -> bytes:
    return PBKDF2HMAC(hashes.SHA256(), 32, salt, iteraciones).derive(password.encode("utf-8"))


def cifrar(datos: dict, password: str) -> bytes:
    salt, iv = os.urandom(16), os.urandom(12)
    plano = gzip.compress(json.dumps(datos, ensure_ascii=False, default=str).encode("utf-8"))
    ct = AESGCM(_clave(password, salt, ITERACIONES)).encrypt(iv, plano, None)
    b64 = lambda b: base64.b64encode(b).decode()
    return json.dumps({"v": 1, "kdf": "pbkdf2-sha256", "iter": ITERACIONES,
                       "salt": b64(salt), "iv": b64(iv), "ct": b64(ct)}).encode()


def descifrar(contenido: bytes, password: str) -> dict:
    env = json.loads(contenido)
    d = base64.b64decode
    clave = _clave(password, d(env["salt"]), int(env["iter"]))
    plano = AESGCM(clave).decrypt(d(env["iv"]), d(env["ct"]), None)
    return json.loads(gzip.decompress(plano))


def pedir_password() -> str:
    """Se pide en cada corrida y no se guarda en ningún lado."""
    while True:
        p = getpass.getpass(f"Contraseña para cifrar el dashboard del celular (mín. {LARGO_MINIMO} caracteres): ")
        if len(p) < LARGO_MINIMO:
            print("  Muy corta. Usá una frase larga, por ejemplo cuatro palabras al azar.")
            continue
        if getpass.getpass("Repetila: ") != p:
            print("  No coinciden.")
            continue
        return p
