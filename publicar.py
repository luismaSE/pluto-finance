"""Publica el dashboard cifrado (cartera.enc) en GitHub o Google Drive para la app del celular.

La configuración está en config.toml (copiá config.example.toml). Los tokens NO se guardan:
se leen de una variable de entorno o se piden en la terminal.
"""
import base64
import getpass
import json
import os
import tomllib
from pathlib import Path

import requests

CONFIG = Path("config.toml")
ESTADO = Path(".estado_publicacion.json")


def cargar_config() -> dict:
    if not CONFIG.exists():
        return {}
    with CONFIG.open("rb") as f:
        return tomllib.load(f)


def _estado():
    return json.loads(ESTADO.read_text()) if ESTADO.exists() else {}


def _guardar_estado(e):
    ESTADO.write_text(json.dumps(e, indent=1))


def a_github(contenido: bytes, cfg: dict):
    repo, ruta, rama = cfg["repo"], cfg.get("ruta", "cartera.enc"), cfg.get("rama", "main")
    token = os.environ.get(cfg.get("token_env", "CARTERA_GITHUB_TOKEN")) or \
        getpass.getpass(f"Token de GitHub con permiso de escritura en {repo} (no se guarda): ")
    h = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json",
         "X-GitHub-Api-Version": "2022-11-28"}
    url = f"https://api.github.com/repos/{repo}/contents/{ruta}"
    r = requests.get(url, headers=h, params={"ref": rama}, timeout=30)
    sha = r.json().get("sha") if r.status_code == 200 else None
    body = {"message": "Actualizar cartera cifrada", "branch": rama,
            "content": base64.b64encode(contenido).decode()}
    if sha:
        body["sha"] = sha
    r = requests.put(url, headers=h, json=body, timeout=60)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"GitHub respondió {r.status_code}: {r.text[:300]}")
    print(f"  ✓ Subido a github.com/{repo}/{ruta} (rama {rama})")


def a_drive(contenido: bytes, cfg: dict):
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaInMemoryUpload
    except ImportError:
        raise RuntimeError("Faltan librerías de Drive: pip install -r requirements-drive.txt")
    # drive.file: la app solo puede ver los archivos que ella misma creó, nada más de tu Drive.
    flow = InstalledAppFlow.from_client_secrets_file(cfg["client_secret"], ["https://www.googleapis.com/auth/drive.file"])
    print("  Se abre el navegador para autorizar Google Drive (el permiso no se guarda).")
    creds = flow.run_local_server(port=0, open_browser=True)
    svc = build("drive", "v3", credentials=creds, cache_discovery=False)
    media = MediaInMemoryUpload(contenido, mimetype="application/octet-stream")
    est = _estado()
    fid = est.get("drive_file_id")
    if fid:
        svc.files().update(fileId=fid, media_body=media).execute()
    else:
        meta = {"name": cfg.get("nombre", "cartera.enc")}
        fid = svc.files().create(body=meta, media_body=media, fields="id").execute()["id"]
        # Link de solo lectura: el contenido está cifrado, quien tenga el link solo ve datos ilegibles.
        svc.permissions().create(fileId=fid, body={"type": "anyone", "role": "reader"}).execute()
        est["drive_file_id"] = fid
        _guardar_estado(est)
    print(f"  ✓ Subido a Google Drive. ID del archivo (cargalo en la app): {fid}")


def publicar(contenido: bytes):
    cfg = cargar_config().get("publicar", {})
    destino = cfg.get("destino", "ninguno")
    Path("salida").mkdir(exist_ok=True)
    Path("salida/cartera.enc").write_bytes(contenido)
    print("  Copia local: salida/cartera.enc")
    if destino == "github":
        a_github(contenido, cfg["github"])
    elif destino == "drive":
        a_drive(contenido, cfg["drive"])
    else:
        print("  Sin destino configurado (config.toml → [publicar] destino). Pasá el archivo al celular a mano.")
