# Cómo colaborar

## Sumar un banco, billetera o broker

La forma más útil de ayudar es sumar el lector del resumen de tu banco. **Nunca subas PDFs reales ni datos personales al repo.**

1. Sacá el texto de tu resumen, anonimizado:
   ```bash
   python herramientas/texto_pdf.py mi-resumen.pdf --anonimizar > ejemplo.txt
   ```
   Cambia todas las cifras y los nombres propios, pero conserva el formato. **Revisá el archivo** antes de compartirlo: si quedó algún nombre, CBU o dirección, borralo a mano.
2. Copiá `conectores/pdf/_plantilla.py` como `conectores/pdf/mi_banco.py` y completá `detectar()` y `parsear()`. Usá de ejemplo `galicia_caja.py` (cuenta), `galicia_fci.py` (fondos) o `mercadopago.py`.
3. Agregalo a `PARSERS` en `conectores/pdf/__init__.py`.
4. Sumá una prueba en `tests/test_lectores.py` con un texto **inventado** con el mismo formato (mirá los ejemplos que ya hay).
5. Corré las pruebas: `python -m pytest`.

Si no programás, abrí un *issue* con el texto anonimizado del paso 1 y el nombre del banco.

Para un broker con API: `conectores/brokers/_plantilla.py`. Para un proveedor de IA: `ia/_plantilla.py`.

## Antes de mandar cambios
- `python -m pytest` tiene que pasar.
- Si cambiás `plantillas/dashboard/`, regenerá el dashboard: `python plantillas/ensamblar.py` (una prueba verifica que esté al día).
- Escribí en castellano, con mensajes claros para quien usa la app.
- Revisá que no haya datos tuyos en comentarios, ejemplos ni pruebas.
