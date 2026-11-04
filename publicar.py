"""Publica el dashboard cifrado (cartera.enc) en GitHub o Google Drive para la app del celular."""
import base64
import getpass
import json
import os
from pathlib import Path

import requests

ESTADO = Path(".estado_publicacion.json")


def _estado():
    return json.loads(ESTADO.read_text()) if ESTADO.exists() else {}


def _guardar_estado(e):
    ESTADO.write_text(json.dumps(e, indent=1))


def _headers(token):
    return {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"}


def token_github(cfg_gh: dict, token: str | None = None, preguntar=True) -> str | None:
    """Orden: parámetro (llavero) -> variable de entorno -> se pide en la terminal."""
    if token:
        return token
    t = os.environ.get(cfg_gh.get("token_env", "CARTERA_GITHUB_TOKEN"))
    if t:
        return t
    if preguntar:
        return getpass.getpass(f"Token de GitHub con permiso de escritura en {cfg_gh['repo']} (no se guarda): ")
    return None


def probar_github(cfg_gh: dict, token: str) -> str:
    """Verifica que el token pueda escribir en el repo. Devuelve un mensaje legible."""
    r = requests.get(f"https://api.github.com/repos/{cfg_gh['repo']}", headers=_headers(token), timeout=20)
    if r.status_code == 401:
        raise RuntimeError("Token inválido o vencido")
    if r.status_code == 404:
        raise RuntimeError("No encuentro el repo (o el token no tiene acceso a él)")
    r.raise_for_status()
    d = r.json()
    if not d.get("permissions", {}).get("push", False):
        raise RuntimeError("El token puede leer pero no escribir: dale permiso Contents: Read and write")
    aviso = "" if d.get("private") else "  ⚠ El repo es PÚBLICO: conviene hacerlo privado."
    return f"Conexión correcta con {d['full_name']} (rama {d.get('default_branch')}).{aviso}"


def a_github(contenido: bytes, cfg_gh: dict, token: str, log=print):
    repo, ruta, rama = cfg_gh["repo"], cfg_gh.get("ruta", "cartera.enc"), cfg_gh.get("rama", "main")
    h = _headers(token)
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    r = requests.get(url, headers=h, params={"ref": rama}, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": "Actualizar cartera cifrada", "branch": rama, "content": base64.b64encode(contenido).decode()}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=h, json=body, timeout=60)
    if r.status_code == 404 and not sha:
        # repo vacío o rama inexistente: se intenta sin rama para crear el primer commit
        body.pop("branch")
        r = requests.put(url, headers=h, json=body, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub respondió {r.status_code}: {r.text[:300]}")
    log(f"  ✓ Subido a github.com/{repo}/{ruta}")


def a_drive(contenido: bytes, cfg_drive: dict, log=print):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload
    except ImportError:
        raise RuntimeError("Faltan librerías de Drive: pip install -r requirements-drive.txt")
    # drive.file: solo puede ver los archivos que esta app creó, nada más de tu Drive.
    flow = InstalledAppFlow.from_client_secrets_file(cfg_drive["client_secret"], ["https://www.googleapis.com/auth/drive.file"])
    log("  Se abre el navegador para autorizar Google Drive (el permiso no se guarda).")
    creds = flow.run_local_server(port=0, open_browser=True)
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    media = MediaInMemoryUpload(contenido, mimetype="application/octet-stream")
    est = _estado()
    fid = est.get("drive_file_id")
    if fid:
        svc.files().update(fileId=fid, media_body=media).execute()
    else:
        fid = svc.files().create(body={"name": cfg_drive.get("nombre", "cartera.enc")}, media_body=media, fields="id").execute()["id"]
        # Link de solo lectura: el contenido está cifrado, quien tenga el link solo ve datos ilegibles.
        svc.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"}).execute()
        est["drive_file_id"] = fid
        _guardar_estado(est)
    log(f"  ✓ Subido a Google Drive. ID del archivo (cargalo en la app): {fid}")


def publicar(contenido: bytes, cfg_pub: dict, token: str | None = None, log=print, preguntar=True):
    Path("salida").mkdir(exist_ok=True)
    Path("salida/cartera.enc").write_bytes(contenido)
    destino = cfg_pub.get("destino", "ninguno")
    if destino == "github":
        t = token_github(cfg_pub["github"], token, preguntar)
        if not t:
            raise RuntimeError("Falta el token de GitHub (guardalo en Configuración)")
        a_github(contenido, cfg_pub["github"], t, log)
    elif destino == "drive":
        a_drive(contenido, cfg_pub["drive"], log)
    else:
        log("  Sin destino configurado: quedó una copia en salida/cartera.enc para pasar a mano.")
