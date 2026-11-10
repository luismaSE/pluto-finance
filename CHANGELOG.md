# Cambios

## Próxima versión

**Nuevo**
- **¿Le ganás a la inflación?** Compara tu patrimonio con la inflación oficial y con el dólar MEP desde tu primera actualización, con un gráfico de lo que necesitabas para empatarle.
- **Metas de ahorro:** monto en pesos o dólares, fecha y lo ya ahorrado. Pluto te dice cuánto ahorrar por mes y, con tus resúmenes, si llegás o cuándo llegarías.
- **Pagos fijos y aumentos:** detecta suscripciones, servicios y comisiones que se repiten cada mes y avisa cuando suben ("Netflix subió 25%").

**Arreglos**
- Los números del eje del gráfico de patrimonio se cortaban en el celular.

## 1.3.1

**Mejoras**
- **Análisis y Mercado más visuales:** titular de una línea, puntaje de salud financiera, indicadores con semáforo, termómetro de riesgo contra tu perfil, tarjetas de acción y distribución en barras. Los detalles quedan plegados ("Por qué", "Cómo") para leer de un vistazo.
- **Mercado en Inicio:** la app de escritorio muestra el titular del último análisis de mercado, sus recomendaciones y cuántas acertaron.
- La respuesta de la IA se revisa antes de mostrarla: números fuera de rango, listas largas o recomendaciones sin sentido ya no llegan al dashboard.

**Arreglos**
- La pestaña Mercado aparecía vacía cuando no había análisis de mercado.
- Íconos de alerta legibles en amarillo y naranja (antes eran blancos y casi no se veían).

**Para quien colabora**
- Pruebas del dashboard en un navegador: todas las pestañas, celular, modo claro y análisis guardados con el formato anterior. Corren en GitHub en cada cambio.

## 1.3.0

**Nuevo**
- **Análisis de mercado con IA** (pestaña Mercado): distribución sugerida según tu perfil, recomendaciones concretas con riesgos y nivel de confianza, noticias recientes de tus activos y escenarios. Usa precios e historia de IOL y una lista de activos a seguir. Guarda cada recomendación con su precio para ver después si acertó. **Pluto solo analiza y recomienda: nunca opera.**
- **Límites de gasto** mensuales, total y por categoría, con proyección a fin de mes y avisos al 80% y al pasarte.
- **Tarjetas de crédito:** cuenta regresiva hasta el cierre y el vencimiento, con aviso una semana antes. Muestra el último pago detectado.
- **Categorías propias:** página para corregir la categoría de un movimiento; Pluto recuerda la regla.
- **Meta de fondo de emergencia** con barra de avance.
- **Avisos** en Inicio y en el dashboard (vencimientos, límites, resúmenes viejos).
- **Ejecutable de Windows** (`Pluto-windows.zip`, experimental): no hace falta instalar Python.

**Mejoras**
- App Android sin la barra superior: el contenido respeta la barra de estado y la de navegación. Configuración se abre desde la pantalla de desbloqueo y el gesto "atrás" bloquea.
- La conexión con IOL es de solo lectura: el código bloquea cualquier pedido que no sea una consulta.
- Mensajes de error claros (por ejemplo, "No pude conectarme a IOL" en lugar del error técnico).
- Historial y último análisis cifrados en la PC; se conservan solo los últimos dashboards.
- Script para generar la clave de firma del APK y cargarla en GitHub.

**Para quien colabora**
- Licencia MIT, guía para sumar bancos y herramienta para anonimizar resúmenes PDF.
- 53 pruebas automáticas que corren en GitHub en cada cambio.
- La interfaz y el dashboard se separaron en HTML, CSS y JS.

**Cambios internos**
- El identificador de la app Android pasa a `ar.pluto.app`: hay que desinstalar la versión anterior una vez.
- El llavero se llama ahora "pluto"; las claves guardadas se migran solas.

## 1.2.0 — Pluto

**Nueva identidad**
- La app se llama **Pluto**. Logo de la gema, ícono para escritorio y Android (incluido el ícono temático de Android 13), paleta pizarra, granito, óxido, cielo y hueso.
- Tipografías Bricolage Grotesque, IBM Plex Sans e IBM Plex Mono incluidas en la app: se ven igual sin internet.

**App de escritorio**
- Botón "Actualizar todo": importa resúmenes desde Descargas, consulta brokers, analiza con IA, genera el dashboard y lo publica al celular.
- Asistente de bienvenida en el primer uso; claves guardadas en el llavero del sistema.
- Dashboard dentro de la app, aislado de la configuración. Modo oscuro por defecto.
- Descarga asistida de resúmenes de Galicia.
- Instaladores para Linux, macOS y Windows.

**Fuentes de datos**
- Registro de bancos y billeteras (PDF) y brokers (API) con plantillas para sumar nuevos.
- Galicia (caja de ahorro en pesos y dólares, fondos FIMA), Mercado Pago (resumen de cuenta) e IOL (API).

**Análisis con IA**
- Proveedores a elección: Claude Code, API de Anthropic, cualquier API compatible con OpenAI y Ollama (local).
- Si una actualización no corre el análisis, se mantiene el último que salió bien.

**Dashboard**
- Pestañas Resumen, Gastos, Inversiones y Análisis; modo privado para ocultar montos.
- Evolución del patrimonio, ingresos y gastos por mes, costo de la plata quieta, gastos fijos y suscripciones.

**App Android**
- Nombre, ícono y colores de Pluto; modo oscuro por defecto.

## 1.0.0
- Primera versión de la app Android: dashboard cifrado descargado desde GitHub o Google Drive, con desbloqueo por contraseña o huella.
