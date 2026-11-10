# Lista de pruebas manuales

Las pruebas automáticas (`python -m pytest`) cubren los cálculos, los lectores de PDF, el cifrado y el dashboard abierto en un navegador (todas las pestañas, celular, modo claro y análisis viejos; necesita `pip install playwright && python -m playwright install chromium`, si no se saltean). Esto es lo que hay que probar a mano en cada equipo antes de un release.

## App de escritorio
- [ ] `./instalar.sh` (o `instalar.bat`) termina sin errores y crea el acceso directo "Pluto" con el ícono de la gema.
- [ ] La app abre con el asistente de bienvenida la primera vez; al terminarlo se crea `config.toml`.
- [ ] El llavero funciona: Configuración → guardar el token de GitHub → aparece "✓ Guardado en el llavero" y sigue ahí al reabrir la app.
- [ ] **Actualizar todo** con un PDF nuevo en Descargas: lo importa, la consola muestra cada paso y el dashboard se actualiza.
- [ ] IOL (si lo usás): con usuario y clave reales trae saldos y posiciones.
- [ ] Análisis con IA: el botón **Probar** responde con el proveedor elegido.
- [ ] **Descargar de Galicia**: se abre el navegador, el PDF descargado aparece como "resumen nuevo".
- [ ] Categorías: cambiar la categoría de un movimiento y, tras actualizar, el dashboard la respeta.
- [ ] Presupuestos y tarjetas: cargar un límite y una tarjeta; el dashboard muestra la barra y la cuenta regresiva.
- [ ] Modo claro y oscuro se ven bien; el tema elegido se recuerda.

## App Android
- [ ] Instalar el APK del release (desinstalando antes la versión anterior si la firma cambió).
- [ ] El ícono de la gema se ve bien en el escritorio del teléfono y como ícono temático (Android 13+).
- [ ] Configuración → GitHub o Drive → **Probar conexión** da "✓ Conexión correcta".
- [ ] Desbloquear con contraseña; activar huella; cerrar y volver a abrir con huella.
- [ ] Sin internet, muestra la última copia y avisa que no pudo actualizar.
- [ ] No permite capturas de pantalla y se bloquea al salir.

## Publicación al celular
- [ ] `Actualizar todo` con "Publicar al celular": en el repo de datos aparece `cartera.enc` actualizado y la app lo baja.
