# Mi cartera: IOL + Galicia + Mercado Pago → Claude → dashboard

Junta tus saldos, gastos e inversiones, se los pasa a Claude para que los analice y arma un dashboard HTML local.

- **IOL:** en vivo por la API oficial (te pide usuario y clave en la terminal).
- **Galicia y Mercado Pago:** desde los **resúmenes PDF** que descargás vos.

## Seguridad
- **No se guardan credenciales.** La clave de IOL se pide sin mostrarse y se descarta después del login.
- Los PDF y el dashboard quedan solo en tu computadora (`reportes/` y `salida/` están en `.gitignore`).
- **A Claude le llega solo un resumen** (saldos, posiciones, gastos por mes). Los números largos (CBU, CUIT, nros. de operación) se borran antes.

## Instalación
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```
Para el análisis necesitás [Claude Code](https://claude.com/claude-code) instalado y logueado (comando `claude`).
En **IOL** habilitá el acceso por API: Mi cuenta → Personalización → APIs.

## Qué PDFs descargar (y dejar en `reportes/`)
| Entidad | Reporte | Dónde |
|---|---|---|
| Galicia | Resumen de **Caja de Ahorro en Pesos** | Online Banking → Cuentas → Resúmenes |
| Galicia | Resumen de **Caja de Ahorro en Dólares** | Ídem |
| Galicia | **Posición de inversiones** (cuenta comitente / FIMA) | Inversiones → Resúmenes |
| Mercado Pago | **Resumen de cuenta** (`account_statement-*.pdf`) | App → Tu dinero → Resúmenes de cuenta |

Cada PDF se reconoce por su contenido, no por el nombre. Si dejás varios meses, el dashboard usa el saldo más reciente y te deja elegir el mes de gastos.

## Uso
```bash
python main.py                                  # IOL + PDFs de ./reportes
python main.py --reportes ~/Descargas/resumenes # otra carpeta o lista de PDFs
python main.py --sin-iol                        # solo PDFs
python main.py --demo                           # datos ficticios
python main.py --modelo opus --sin-analisis     # opciones de Claude
python main.py --celular                        # además cifra y publica para la app Android
```

## Cómo se calculan los gastos
- Se agrupan **por mes**. Cada resumen cubre un período distinto, así que el dashboard muestra qué fechas cubre cada fuente y marca en gris los días sin reporte.
- **Entre mis cuentas** (no cuenta como gasto ni ingreso): transferencias a/desde tu propio nombre, "Ingreso de dinero" de MP y los DEBIN recurrentes de Galicia (se asume que fondean Mercado Pago).
- **Pago de tarjeta** es el pago del resumen de la tarjeta; el detalle de consumos va en el resumen de la tarjeta.
- Las reglas están en `categorias.py`: agregá palabras clave para tus comercios.
- Cada resumen se valida: si un movimiento no cierra con el saldo, aparece una advertencia.

## Ver el dashboard en el celular (app Android)

```
PC:  python main.py --celular  →  cifra los datos con tu contraseña  →  sube cartera.enc a GitHub o Drive
App: baja cartera.enc  →  pide contraseña o huella  →  descifra en memoria  →  muestra el dashboard
```

**Seguridad**
- El archivo viaja cifrado (AES-256-GCM, clave derivada con PBKDF2-SHA256 de 600.000 iteraciones). Quien acceda a tu almacenamiento solo ve datos ilegibles, y si alguien lo modifica la app lo rechaza.
- El archivo contiene **solo datos**, no código: el dashboard viene dentro de la app.
- Tu contraseña no se guarda en ningún lado. Con la huella, la app la guarda cifrada con una clave del Keystore de Android que solo se libera después de validar la huella. Si agregás una huella nueva al teléfono, esa clave se invalida.
- La app bloquea capturas de pantalla, se bloquea sola al salir, no hace backups a la nube y el dashboard no tiene acceso a internet.
- Usá una contraseña larga (mínimo 12 caracteres; por ejemplo, 4 o 5 palabras al azar).

### 1. Elegí dónde guardar el archivo cifrado

Copiá `config.example.toml` como `config.toml` y elegí `destino`.

**GitHub (recomendado)**
1. Creá un repo **privado** solo para el archivo cifrado, por ejemplo `cartera-datos`.
2. En GitHub → Settings → Developer settings → Fine-grained tokens, creá dos tokens con acceso solo a ese repo:
   - **PC:** permiso *Contents: Read and write*. Cargalo en la variable `CARTERA_GITHUB_TOKEN` o pegalo cuando el script lo pida.
   - **Celular:** permiso *Contents: Read-only*. Se carga en la app.

**Google Drive**
1. En [Google Cloud Console](https://console.cloud.google.com/), creá un proyecto, habilitá *Google Drive API* y creá credenciales OAuth de tipo **App de escritorio**. Descargá el JSON como `client_secret.json`.
2. Ejecutá `pip install -r requirements-drive.txt`.
3. En cada publicación se abre el navegador para autorizar. El permiso es `drive.file`: el script solo ve el archivo que él mismo creó, no el resto de tu Drive.
4. La primera vez se crea el archivo con un link de solo lectura y se muestra su ID: ese ID se carga en la app.

### 2. Instalá la app
1. Desde el celular, entrá a la sección **Releases** del repo y descargá `mi-cartera-vX.Y.Z.apk` de la última versión.
2. Abrilo e instalalo. Android te va a pedir permitir "instalar apps desconocidas" (y Play Protect puede pedir "Instalar de todos modos").
3. Abrí la app → Configuración → cargá GitHub o Drive → **Probar conexión** → Guardar.

Para publicar una versión nueva: creá un release en GitHub (Releases → *Draft a new release*, tag `v1.0.1`) o subí un tag con `git tag v1.0.1 && git push origin v1.0.1`. GitHub Actions compila el APK y lo adjunta al release.

### 3. (Recomendado) Firmá la app con tu propia clave
Sin una clave propia, cada compilación se firma distinto y para actualizar hay que desinstalar la versión anterior. Generá una clave una sola vez:
```bash
keytool -genkeypair -v -keystore cartera.jks -alias cartera -keyalg RSA -keysize 4096 -validity 10000
```
```bash
base64 -w0 cartera.jks
```
En el repo del código → Settings → Secrets and variables → Actions, creá estos secrets: `CARTERA_KEYSTORE_BASE64` (la salida de base64), `CARTERA_KEYSTORE_PASSWORD`, `CARTERA_KEY_ALIAS` (`cartera`) y `CARTERA_KEY_PASSWORD`. Guardá `cartera.jks` en un lugar seguro y **nunca lo subas al repo**.

## Estructura
| Archivo | Qué hace |
|---|---|
| `main.py` | Orquesta todo |
| `conectores/iol.py` | API oficial de IOL |
| `conectores/pdf/galicia_caja.py` | Resumen de caja de ahorro (ARS y USD) |
| `conectores/pdf/galicia_fci.py` | Posición de fondos FIMA / comitente |
| `conectores/pdf/mercadopago.py` | Resumen de cuenta de Mercado Pago |
| `categorias.py` | Reglas de categorías (editables) |
| `cotizaciones.py` | Dólar oficial, MEP, CCL y blue (dolarapi.com) |
| `resumen.py` | Totales, consolidación al MEP y gastos por mes |
| `analisis.py` | Análisis con Claude Code (`claude -p`) |
| `plantillas/dashboard.html` | Dashboard (claro/oscuro, sin internet); lo usan la PC y la app |
| `cifrado.py` | Cifrado del archivo para el celular |
| `publicar.py` | Subida a GitHub o Google Drive |
| `android/` | App Android (Kotlin); se compila con GitHub Actions |

Para soportar otro PDF (por ejemplo el resumen de la tarjeta Visa), agregá un módulo en `conectores/pdf/` con `detectar(texto)` y `parsear(texto)` y sumalo a `PARSERS`.
