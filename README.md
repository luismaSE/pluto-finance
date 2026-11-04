# Mi cartera

Tus bancos, billeteras y brokers en un solo lugar: un dashboard con patrimonio, gastos e inversiones, un análisis hecho por IA y una app para verlo en el celular. Todo corre en tu computadora.

- **Bancos y billeteras** (Galicia y Mercado Pago incluidos): se leen de los **resúmenes PDF** que descargás.
- **Brokers con API** (IOL incluido): se consultan en vivo; usuario y clave se piden cada vez y no se guardan.
- **IA a elección:** Claude Code, API de Anthropic, cualquier API compatible con OpenAI, u **Ollama** (local, los datos no salen de tu equipo).
- Se suman bancos, brokers y proveedores de IA con un archivo cada uno (ver [Sumar fuentes o proveedores](#sumar-bancos-brokers-o-proveedores-de-ia)).

## Instalación rápida

Necesitás **Python 3.11 o más nuevo** ([python.org](https://www.python.org/downloads/)).

**Linux / macOS**
```bash
git clone https://github.com/luismaSE/wallet-dashboard.git
```
```bash
cd wallet-dashboard && ./instalar.sh
```
```bash
./iniciar.sh
```

**Windows:** descargá el repo (Code → Download ZIP), descomprimilo y hacé doble clic en **`instalar.bat`**. Después abrí la app con el acceso directo "Mi cartera" del escritorio o con `iniciar.bat`.

La primera vez se abre un **asistente** que te pregunta en 4 pasos dónde guardar los resúmenes, qué bancos y brokers usás y con qué IA querés el análisis. Todo se puede cambiar después en Configuración.

## App de escritorio

Configurás todo una vez y después es un clic: **Actualizar todo** importa los resúmenes nuevos de tu carpeta de Descargas, consulta tus brokers, hace el análisis con IA, genera el dashboard y lo publica al celular.

- Ventana propia: no abre puertos ni levanta servidores.
- Tokens, claves de API y la contraseña del celular se guardan en el **llavero del sistema** (GNOME Keyring / KWallet en Linux, Credential Manager en Windows, Keychain en macOS), nunca en archivos del proyecto.
- Las claves de los brokers se piden en cada actualización y no se guardan.
- El dashboard se ve dentro de la app, en un marco aislado: no puede leer la configuración ni los secretos, ni conectarse a internet.
- Modo oscuro por defecto (se cambia desde la barra lateral).
- En Linux necesitás un llavero activo (gnome-keyring o kwallet).

La terminal (`python main.py`) sigue funcionando y usa la misma configuración y los mismos secretos guardados.

### Descargar resúmenes de Galicia

En Inicio → **Descargar de Galicia** se abre un navegador **nuevo y vacío** en la web del banco.
1. Iniciás sesión vos (usuario, clave y token). La app no lee ni guarda nada de eso.
2. Descargás o abrís los PDF de los resúmenes: cada uno se reconoce por su contenido y, si es nuevo, se guarda solo en la carpeta de resúmenes.
3. Cerrás el navegador (la sesión se borra) y tocás **Actualizar ahora**.

Necesita Playwright (`pip install -r requirements-descarga.txt` y `playwright install chromium`). Si Galicia bloquea el navegador de Playwright, en Configuración elegí **Google Chrome**.

**Mercado Pago** no tiene descarga asistida: el resumen se genera bajo demanda (tarda varios minutos) y la web bloquea navegadores automatizados. Pedilo desde la web o la app, bajalo a tu carpeta de Descargas y se importa solo al tocar **Actualizar todo**.

También funciona desde la terminal: `python descarga_asistida.py galicia`.

**¿Por qué no es 100% automático?** Para entrar solo, la app tendría que guardar tu clave y saltear el 2FA, lo que va en contra de no guardar credenciales (y de los términos de los bancos). Lo que sí se puede automatizar es la navegación después del login, con una **receta**: un archivo `recetas/galicia.json` con pasos como estos:
```json
[
  {"esperar_url": "onlinebanking\\.bancogalicia\\.com\\.ar/(inicio|home)"},
  {"click": "text=Cuentas"},
  {"click": "text=Resúmenes"}
]
```
Pasos posibles: `esperar_url` (regex), `ir` (url), `click` (selector o `text=...`) y `esperar` (ms). Si un paso falla, la app sigue en modo manual. Los selectores dependen de cómo se ve tu cuenta, así que se arman una vez mirando la web (o grabando los clics con `playwright codegen`, sin incluir los campos de usuario y clave).

## Seguridad
- **No se guardan las claves de bancos ni brokers.** Se piden en cada actualización y se descartan después del login.
- Los PDF y el dashboard quedan solo en tu computadora (`reportes/` y `salida/` están en `.gitignore`).
- **A la IA le llega solo un resumen** (saldos, posiciones, gastos por mes). Los números largos (CBU, CUIT, nros. de operación) se borran antes. Con Ollama no sale nada de tu equipo.

## Análisis con IA

Se elige en Configuración → Análisis con IA (o en el asistente). Cada proveedor tiene su modelo y, si hace falta, su clave (guardada en el llavero).

| Proveedor | Qué necesitás |
|---|---|
| **Claude Code** | [Claude Code](https://claude.com/claude-code) instalado y con sesión iniciada (comando `claude`). Sin clave aparte. |
| **Claude (API de Anthropic)** | Una clave de [console.anthropic.com](https://console.anthropic.com). Modelo por defecto: `claude-opus-5-5`. |
| **API compatible con OpenAI** | Dirección del servidor, modelo y clave. Sirve para OpenAI, OpenRouter, Gemini, LM Studio, etc. |
| **Ollama (local)** | [Ollama](https://ollama.com) corriendo y un modelo descargado (`ollama pull llama3.1`). |

Prueba rápida del proveedor configurado: `python analisis.py` (o el botón **Probar** en la app). Si una actualización no corre el análisis (o falla), se muestra el último que salió bien, con su fecha.

## Instalación manual
```bash
python -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r requirements-escritorio.txt
playwright install chromium    # solo para la descarga asistida
```
Solo terminal, sin app: `pip install -r requirements.txt`.

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
python main.py                                  # brokers activos + PDFs de ./reportes
python main.py --reportes ~/Descargas/resumenes # otra carpeta o lista de PDFs
python main.py --sin-brokers                    # solo PDFs
python main.py --demo                           # datos ficticios
python main.py --proveedor ollama --modelo llama3.1   # otro proveedor de IA
python main.py --sin-analisis                   # sin IA
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

## Sumar bancos, brokers o proveedores de IA

Cada fuente es un archivo; la app los muestra solos en Configuración y en el asistente.

| Querés sumar | Copiá | Y agregalo a |
|---|---|---|
| Un banco o billetera con resúmenes PDF | `conectores/pdf/_plantilla.py` | `PARSERS` en `conectores/pdf/__init__.py` |
| Un broker con API | `conectores/brokers/_plantilla.py` | `BROKERS` en `conectores/brokers/__init__.py` |
| Un proveedor de IA | `ia/_plantilla.py` | `PROVEEDORES` en `ia/__init__.py` |

Para ver el texto de un PDF y armar el lector: `python -c "from conectores.pdf import leer_texto; print(leer_texto('resumen.pdf'))"`. Antes de compartir un lector, sacá cualquier dato tuyo de los comentarios y ejemplos.

## Estructura
| Archivo | Qué hace |
|---|---|
| `app.py`, `escritorio/` | App de escritorio (pywebview) |
| `main.py` | Uso desde la terminal |
| `pipeline.py` | El proceso completo, compartido por la app y la terminal |
| `configuracion.py` | config.toml + llavero del sistema |
| `importar.py` | Importa resúmenes nuevos desde Descargas |
| `historial.py` | Totales de cada corrida para la evolución del patrimonio |
| `conectores/brokers/` | Brokers con API (IOL) |
| `fuentes.py` | Catálogo de bancos, billeteras y brokers |
| `ia/` | Proveedores de IA (Claude Code, Anthropic, OpenAI compatible, Ollama) |
| `conectores/pdf/galicia_caja.py` | Resumen de caja de ahorro (ARS y USD) |
| `conectores/pdf/galicia_fci.py` | Posición de fondos FIMA / comitente |
| `conectores/pdf/mercadopago.py` | Resumen de cuenta de Mercado Pago |
| `categorias.py` | Reglas de categorías (editables) |
| `cotizaciones.py` | Dólar oficial, MEP, CCL y blue (dolarapi.com) |
| `resumen.py` | Totales, consolidación al MEP y gastos por mes |
| `instalar.sh`, `instalar.bat` | Instaladores (Linux/macOS y Windows) |
| `plantillas/dashboard.html` | Dashboard (claro/oscuro, sin internet); lo usan la PC y la app |
| `cifrado.py` | Cifrado del archivo para el celular |
| `publicar.py` | Subida a GitHub o Google Drive |
| `android/` | App Android (Kotlin); se compila con GitHub Actions |

Para soportar otro PDF (por ejemplo el resumen de la tarjeta Visa), agregá un módulo en `conectores/pdf/` con `detectar(texto)` y `parsear(texto)` y sumalo a `PARSERS`.
