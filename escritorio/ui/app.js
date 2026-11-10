const $ = s => document.querySelector(s), $$ = s => [...document.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nf0 = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 });
const compact = n => n == null ? '—' : Math.abs(n) >= 1e6 ? '$ ' + (n / 1e6).toFixed(2).replace('.', ',').replace(/,00$/, '') + ' M' : '$ ' + nf0.format(n);
const fecha = iso => iso ? new Date(iso).toLocaleString('es-AR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '—';
let API = null, EST = null, corriendo = false;

// ---------- navegación ----------
// ---------- límites de gasto ----------
const NO_LIMITABLES = new Set(['Entre mis cuentas', 'Sueldo', 'Rendimientos']);
function llenarLimites(c) {
  const p = c.presupuestos || {}, cats = (EST.categorias || []).filter(x => !NO_LIMITABLES.has(x));
  $('#lim-total').value = p.total || '';
  $('#lim-categorias').innerHTML = cats.map(x => `<label>${esc(x)}<input type="number" min="0" step="1000" data-lim="${esc(x)}" value="${(p.categorias || {})[x] || ''}" placeholder="Sin límite"></label>`).join('');
}
function leerLimites() {
  const cats = {};
  $$('[data-lim]').forEach(i => { const v = parseFloat(i.value); if (v > 0) cats[i.dataset.lim] = v; });
  return { total: parseFloat($('#lim-total').value) || 0, categorias: cats };
}

// ---------- metas de ahorro ----------
function filaObjetivo(o = {}) {
  const d = document.createElement('div');
  d.className = 'objetivo-cfg';
  d.innerHTML = `<label>Meta<input data-o="nombre" placeholder="Viaje" value="${esc(o.nombre || '')}"></label>
    <label>Monto<input data-o="monto" type="number" min="0" step="any" value="${o.monto || ''}"></label>
    <label>Moneda<select data-o="moneda"><option value="ARS">Pesos</option><option value="USD" ${o.moneda === 'USD' ? 'selected' : ''}>Dólares</option></select></label>
    <label>Para cuándo<input data-o="fecha" type="date" value="${esc(o.fecha || '')}"></label>
    <label>Ya ahorrado<input data-o="ahorrado" type="number" min="0" step="any" value="${o.ahorrado || ''}" placeholder="0"></label>
    <button class="btn peligro" type="button" title="Quitar">Quitar</button>`;
  d.querySelector('button').onclick = () => d.remove();
  $('#objetivos-filas').appendChild(d);
}
function llenarObjetivos(c) {
  $('#objetivos-filas').innerHTML = '';
  Object.values(c.objetivos || {}).forEach(filaObjetivo);
}
$('#btn-agregar-objetivo').onclick = () => filaObjetivo();
function leerObjetivos() {
  const valor = {};
  for (const f of $$('.objetivo-cfg')) {
    const g = k => f.querySelector(`[data-o="${k}"]`).value.trim();
    const nombre = g('nombre');
    if (!nombre) continue;
    const monto = parseFloat(g('monto')), ahorrado = parseFloat(g('ahorrado')) || 0;
    if (!(monto > 0)) return { error: `${nombre}: cargá el monto de la meta` };
    if (!g('fecha')) return { error: `${nombre}: elegí para cuándo` };
    if (ahorrado < 0) return { error: `${nombre}: lo ahorrado no puede ser negativo` };
    let id = nombre.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'meta';
    while (valor[id]) id += '_2';
    valor[id] = { nombre, monto, moneda: g('moneda'), fecha: g('fecha'), ahorrado };
  }
  return { valor };
}

// ---------- tarjetas ----------
function filaTarjeta(t = {}) {
  const d = document.createElement('div');
  d.className = 'tarjeta-cfg';
  d.innerHTML = `<label>Nombre<input data-t="nombre" placeholder="Visa Galicia" value="${esc(t.nombre || '')}"></label>
    <label>Cierra el día<input data-t="cierre" type="number" min="1" max="31" value="${t.cierre || ''}"></label>
    <label>Vence el día<input data-t="vencimiento" type="number" min="1" max="31" value="${t.vencimiento || ''}"></label>
    <label>Fecha exacta de cierre<input data-t="proximo_cierre" type="date" value="${esc(t.proximo_cierre || '')}"></label>
    <label>Fecha exacta de vencimiento<input data-t="proximo_vencimiento" type="date" value="${esc(t.proximo_vencimiento || '')}"></label>
    <button class="btn peligro" type="button" title="Quitar">Quitar</button>`;
  d.querySelector('button').onclick = () => d.remove();
  $('#tarjetas-filas').appendChild(d);
}
function llenarTarjetas(c) {
  $('#tarjetas-filas').innerHTML = '';
  Object.values(c.tarjetas || {}).forEach(filaTarjeta);
}
$('#btn-agregar-tarjeta').onclick = () => filaTarjeta();
function leerTarjetas() {
  const valor = {};
  for (const f of $$('.tarjeta-cfg')) {
    const g = k => f.querySelector(`[data-t="${k}"]`).value.trim();
    const nombre = g('nombre');
    if (!nombre) continue;
    const t = { nombre };
    for (const k of ['cierre', 'vencimiento']) {
      const n = parseInt(g(k), 10);
      if (g(k) && !(n >= 1 && n <= 31)) return { error: `${nombre}: el día de ${k} tiene que estar entre 1 y 31` };
      if (n) t[k] = n;
    }
    for (const k of ['proximo_cierre', 'proximo_vencimiento']) if (g(k)) t[k] = g(k);
    if (!t.cierre && !t.vencimiento && !t.proximo_cierre && !t.proximo_vencimiento) return { error: `${nombre}: cargá al menos un día de cierre o de vencimiento` };
    let id = nombre.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/[^a-z0-9]+/g, '_').replace(/^_|_$/g, '') || 'tarjeta';
    while (valor[id]) id += '_2';
    valor[id] = t;
  }
  return { valor };
}

// ---------- categorías ----------
let CAT = null;
async function cargarCategorias() {
  CAT = await API.categorias();
  pintarCategorias();
}
function pintarCategorias() {
  if (!CAT) return;
  if (!CAT.hay_datos) { $('#cat-lista').innerHTML = '<p class="empty">Todavía no hay movimientos. Corré "Actualizar todo" desde Inicio.</p>'; return; }
  const f = $('#cat-filtro').value, q = $('#cat-buscar').value.trim().toLowerCase();
  const lista = CAT.movimientos.filter(m =>
    (f === 'todos' || (f === 'propias' ? m.propia : ['Otros', 'Transferencias'].includes(m.categoria)))
    && (!q || m.descripcion.toLowerCase().includes(q)));
  const fmt = (n, mon) => (n < 0 ? '−' : '') + (mon === 'USD' ? 'US$ ' : '$ ') + nf0.format(Math.abs(n));
  $('#cat-lista').innerHTML = lista.map((m, i) => `<div class="cat-fila ${m.propia ? 'propia' : ''}">
      <span class="empty">${esc(m.fecha.slice(8, 10) + '/' + m.fecha.slice(5, 7))}</span>
      <span class="desc">${esc(m.descripcion)}<small>${esc(m.entidad)}${m.propia ? ' · regla propia' : ''}</small></span>
      <span class="num">${esc(fmt(m.monto, m.moneda))}</span>
      <select data-i="${CAT.movimientos.indexOf(m)}">${CAT.categorias.map(c => `<option ${c === m.categoria ? 'selected' : ''}>${esc(c)}</option>`).join('')}</select>
    </div>`).join('') || '<p class="empty">No hay movimientos para revisar con este filtro.</p>';
  $$('#cat-lista select').forEach(s => s.onchange = async () => {
    const m = CAT.movimientos[+s.dataset.i];
    const r = await API.guardar_regla(m.descripcion, s.value);
    $('#msg-cat').className = 'msg ' + (r.ok ? 'ok' : 'err');
    $('#msg-cat').textContent = r.ok ? `✓ "${m.descripcion.slice(0, 40)}" → ${s.value}. Se aplica en la próxima actualización.` : '✗ ' + r.error;
    if (r.ok) { m.categoria = s.value; m.propia = true; s.closest('.cat-fila').classList.add('propia'); }
  });
}
$('#cat-filtro').onchange = pintarCategorias;
$('#cat-buscar').oninput = pintarCategorias;

function ir(pag, pestana) {
  $$('aside .nav').forEach(b => b.setAttribute('aria-current', b.dataset.pag === pag));
  $$('.pagina').forEach(p => p.hidden = p.id !== 'pag-' + pag);
  document.querySelector('main').classList.toggle('con-dash', pag === 'dashboard');
  if (pag === 'dashboard') cargarDashboard(pestana);
  if (pag === 'categorias') cargarCategorias();
}
$$('aside .nav').forEach(b => b.onclick = () => ir(b.dataset.pag));

// ---------- consola (la llama Python) ----------
const ui = {
  log(t) {
    const c = $('#consola'), linea = document.createElement('div');
    linea.textContent = t;
    if (/^\s*✓|^\s*\+/.test(t)) linea.className = 'ok';
    else if (/✗|Error|error/.test(t)) linea.className = 'err';
    else if (/^\s*=== |^\n?=== /.test(t)) linea.className = 'tit';
    c.appendChild(linea); c.scrollTop = c.scrollHeight;
  },
  async fin(r) {
    corriendo = false;
    $('#btn-actualizar').disabled = false;
    $('#estado-run').innerHTML = r.ok ? `✓ Terminado${r.celular ? (r.publicado ? ' · publicado al celular' : ' · <span style="color:var(--neg-text)">no se pudo publicar</span>') : ''}` : '<span style="color:var(--neg-text)">✗ Falló</span>';
    ui.log(r.ok ? '\n✓ Listo.' : '\n✗ La actualización falló: ' + (r.error || ''));
    await refrescar();
  },
};
ui.finDescarga = async r => {
  corriendo = false;
  $$('[data-descargar]').forEach(b => b.disabled = false);
  $('#btn-actualizar').disabled = false;
  const n = (r.nuevos || []).length;
  $('#msg-descarga').className = 'msg ' + (r.ok ? 'ok' : 'err');
  $('#msg-descarga').innerHTML = !r.ok ? '✗ ' + esc(r.error || 'Falló')
    : n ? `✓ ${n} ${n > 1 ? 'resúmenes' : 'resumen'} nuevo${n > 1 ? 's' : ''}. <button class="btn primario" id="btn-act-ahora" style="margin-left:8px">Actualizar ahora</button>`
    : 'No se descargaron resúmenes nuevos.';
  const b = $('#btn-act-ahora'); if (b) b.onclick = () => $('#btn-actualizar').click();
};
window.ui = ui;

// ---------- tema (oscuro por defecto, se guarda en la configuración) ----------
const tema = () => document.documentElement.dataset.theme === 'light' ? 'light' : 'dark';
function aplicarTema(t) {
  if (t === 'light') document.documentElement.dataset.theme = 'light'; else delete document.documentElement.dataset.theme;
  $('#txt-tema').textContent = t === 'light' ? 'Modo oscuro' : 'Modo claro';
}
$('#btn-tema').onclick = async () => {
  const t = tema() === 'light' ? 'dark' : 'light';
  aplicarTema(t);
  await API.guardar_config({ ui: { tema: t } });
  if (!$('#pag-dashboard').hidden) cargarDashboard();
};

// ---------- estado ----------
async function refrescar() {
  EST = await API.estado();
  $('#version').textContent = 'v' + EST.version;
  const c = EST.config;
  aplicarTema(c.ui?.tema || 'dark');
  const activos = EST.fuentes.filter(f => f.metodo === 'api' && f.activo);
  $('#lbl-brokers').hidden = !activos.length;
  $('#txt-brokers').textContent = 'Consultar ' + activos.map(f => f.nombre).join(', ');
  $('#op-brokers').checked = activos.length > 0;
  $('#botones-descarga').innerHTML = EST.descarga_sitios.map(x => `<button class="btn" data-descargar="${esc(x.id)}" style="margin-right:8px">Descargar de ${esc(x.nombre)}</button>`).join('');
  $$('[data-descargar]').forEach(b => b.onclick = () => descargar(b));
  $('#op-analisis').checked = c.analisis.activado;
  $('#op-mercado').checked = !!c.mercado?.activado;
  $('#op-celular').checked = c.publicar.destino !== 'ninguno';
  $('#op-celular').disabled = c.publicar.destino === 'ninguno';
  $('#op-celular').parentElement.title = c.publicar.destino === 'ninguno' ? 'Configurá un destino en Configuración → Celular' : '';

  $('#aviso-llavero').innerHTML = EST.llavero.ok ? '' :
    `<div class="aviso"><b>No hay llavero disponible:</b> ${esc(EST.llavero.detalle)}. Los secretos no se pueden guardar y la publicación al celular no va a funcionar desde la app.</div>`;

  const u = EST.historial[0];
  const av = (u && u.avisos) || [];
  $('#card-avisos').hidden = !av.length;
  const colAv = { alta: 'var(--critical)', media: 'var(--warning)', baja: 'var(--sky)' };
  $('#avisos').innerHTML = av.map(a => `<div class="aviso-i"><i style="background:${colAv[a.nivel] || colAv.baja}"></i><div><b>${esc(a.titulo)}</b><div class="d">${esc(a.detalle)}</div></div></div>`).join('')
    + (av.length ? '<p class="empty" style="font-size:12px;margin:8px 0 0">De la última actualización.</p>' : '');

  pintarMercado(EST.mercado);

  $('#ultima').innerHTML = u ? `<div class="kpis">
      <div class="kpi"><div class="l">Patrimonio</div><div class="v">${compact(u.patrimonio_ars)}</div><div class="n">${u.patrimonio_usd ? 'US$ ' + nf0.format(u.patrimonio_usd) : ''}</div></div>
      <div class="kpi"><div class="l">En cuentas</div><div class="v">${compact(u.liquidez_ars)}</div></div>
      <div class="kpi"><div class="l">Invertido</div><div class="v">${compact(u.inversiones_ars)}</div></div></div>
      <p class="empty" style="margin:12px 0 0">${esc(fecha(u.fecha))}</p>` : '<div class="empty">Todavía no actualizaste.</div>';

  $('#fuentes').innerHTML = EST.fuentes.map(f => {
    const n = f.nombre, ok = u && u.fuentes_ok.includes(n), err = u && u.fuentes_error[n];
    const color = ok ? 'var(--good)' : err ? 'var(--critical)' : 'var(--border)';
    const txt = ok ? 'OK en la última actualización' : err ? esc(err) : (f.metodo === 'api' && !f.activo ? 'Desactivado' : 'Sin datos');
    return `<div class="fuente"><span class="dot" style="background:${color}"></span><b>${esc(n)}</b><span class="empty">${txt}</span></div>`;
  }).join('') + `<div class="acciones" style="margin-top:8px"><button class="btn" data-carpeta="reportes">Abrir carpeta de resúmenes</button></div>`;

  $('#tabla-hist').innerHTML = EST.historial.map(h => `<tr><td>${esc(fecha(h.fecha))}</td><td class="num">${compact(h.patrimonio_ars)}</td>
    <td class="num">${h.patrimonio_usd ? 'US$ ' + nf0.format(h.patrimonio_usd) : '—'}</td><td>${esc(h.fuentes_ok.join(', '))}</td>
    <td style="color:var(--neg-text)">${esc(Object.keys(h.fuentes_error || {}).join(', '))}</td></tr>`).join('') || '<tr><td colspan="5" class="empty">Sin actualizaciones todavía.</td></tr>';

  armarConfigDinamica();
  llenarConfig(c);
  llenarLimites(c);
  llenarObjetivos(c);
  llenarTarjetas(c);
  pintarSecretos();
  if (EST.primer_uso && !window._bienvenidaMostrada) { window._bienvenidaMostrada = true; abrirBienvenida(); }
  $$('[data-carpeta]').forEach(b => b.onclick = () => API.abrir_carpeta(b.dataset.carpeta));
}

// ---------- actualizar ----------
const brokersActivos = () => EST.fuentes.filter(f => f.metodo === 'api' && f.activo);
$('#btn-actualizar').onclick = () => {
  if (corriendo) return;
  const activos = brokersActivos();
  if ($('#op-brokers').checked && activos.length) {
    $('#campos-brokers').innerHTML = activos.map(b => `<fieldset style="border:0;padding:0;margin:0 0 6px"><legend style="font-weight:600;margin-bottom:6px">${esc(b.nombre)}</legend>
      ${b.campos.map(c => `<input data-broker="${esc(b.id)}" data-campo="${esc(c.id)}" type="${c.secreto ? 'password' : 'text'}" placeholder="${esc(c.etiqueta)}" autocomplete="off" required>`).join('')}</fieldset>`).join('');
    $('#modal-brokers').hidden = false;
    const primero = $('#campos-brokers input'); if (primero) primero.focus();
  } else lanzar(null);
};
const limpiarBrokers = () => { $$('#campos-brokers input').forEach(i => i.value = ''); $('#campos-brokers').innerHTML = ''; $('#modal-brokers').hidden = true; };
$('#form-brokers').onsubmit = e => {
  e.preventDefault();
  const cred = {};
  $$('#campos-brokers input').forEach(i => { (cred[i.dataset.broker] = cred[i.dataset.broker] || {})[i.dataset.campo] = i.value.trim ? (i.type === 'password' ? i.value : i.value.trim()) : i.value; });
  limpiarBrokers();
  lanzar(cred);
};
$('#brk-omitir').onclick = () => { limpiarBrokers(); lanzar(null); };
$('#brk-cancelar').onclick = limpiarBrokers;

async function lanzar(cred) {
  const op = { consultar_brokers: !!cred, brokers: cred || {}, analisis: $('#op-analisis').checked, mercado: $('#op-mercado').checked, celular: $('#op-celular').checked && !$('#op-celular').disabled };
  $('#consola').innerHTML = '';
  const r = await API.actualizar(op);
  op.brokers = null; cred = null;
  if (!r.ok) { ui.log('✗ ' + r.error); return; }
  corriendo = true;
  $('#btn-actualizar').disabled = true;
  $('#estado-run').innerHTML = '<span class="spinner"></span> Actualizando…';
}

// ---------- descarga asistida ----------
async function descargar(b) {
  if (corriendo) return;
  $('#consola').innerHTML = '';
  const r = await API.descargar(b.dataset.descargar);
  if (!r.ok) { $('#msg-descarga').className = 'msg err'; $('#msg-descarga').textContent = '✗ ' + r.error; return; }
  corriendo = true;
  $$('[data-descargar]').forEach(x => x.disabled = true);
  $('#btn-actualizar').disabled = true;
  $('#msg-descarga').className = 'msg';
  $('#msg-descarga').innerHTML = '<span class="spinner" style="display:inline-block;vertical-align:middle"></span> Esperando que descargues los PDF y cierres el navegador…';
}

// ---------- mercado en Inicio (solo lectura: Pluto recomienda, nunca opera) ----------
const ACC_INI = { comprar: ['var(--good)', '▲'], aumentar: ['var(--good)', '▲'], vender: ['var(--critical)', '▼'],
  reducir: ['var(--warning)', '▼'], cambiar: ['var(--sky)', '⇄'], mantener: ['var(--text-3)', '='] };
function pintarMercado(m) {
  $('#card-mercado').hidden = !m || (!m.titular && !m.error);
  if ($('#card-mercado').hidden) return;
  if (m.error) { $('#mercado-ini').innerHTML = `<div class="empty">El último análisis de mercado falló: ${esc(m.error)}</div>`; return; }
  const ac = m.aciertos || {};
  const recos = (m.recomendaciones || []).map(r => { const [c, i] = ACC_INI[r.accion] || ACC_INI.mantener;
    return `<span class="mk-reco"><b style="color:${c}">${i}</b> ${esc(r.accion)} <b>${esc(r.activo)}</b>${r.por ? ' → <b>' + esc(r.por) + '</b>' : ''}</span>`; }).join('');
  $('#mercado-ini').innerHTML = `<div class="mk-tit">${esc(m.titular)}</div>
    ${recos ? `<div class="mk-recos">${recos}</div>` : ''}
    <div class="mk-pie"><span>${ac.medibles ? `<b>${ac.aciertos} de ${ac.medibles}</b> recomendaciones acertaron` : 'Las recomendaciones se miden a los 7 días'}</span>
      <span class="empty">${m.fecha ? esc(fecha(m.fecha)) : ''}${m.anterior ? ' · análisis anterior' : ''}</span>
      <button class="btn" id="btn-ver-mercado">Ver en el dashboard</button></div>
    <p class="empty" style="font-size:12px;margin:8px 0 0">Pluto solo recomienda: vos decidís y operás en tu broker.</p>`;
  $('#btn-ver-mercado').onclick = () => ir('dashboard', 'mercado');
}

// ---------- dashboard ----------
async function cargarDashboard(pestana) {
  let html = await API.dashboard_html();
  $('#marco').hidden = !html; $('#sin-dash').hidden = !!html;
  if (!html) return;
  // mismo tema que la app
  html = html.replace('<html lang="es" data-theme="dark">', `<html lang="es" data-theme="${tema()}">`);
  const v = String(html.length) + tema();
  const marco = $('#marco');
  const mostrar = () => pestana && marco.contentWindow.postMessage({ ir: pestana }, '*');
  if (marco.dataset.v !== v) { marco.onload = mostrar; marco.srcdoc = html; marco.dataset.v = v; }
  else mostrar();
}
$('#btn-ver-dash').onclick = () => ir('dashboard');
$('#btn-navegador').onclick = () => API.abrir_dashboard_navegador();

// ---------- configuración armada según el catálogo ----------
const TIPOS = { banco: 'Banco', billetera: 'Billetera', broker: 'Broker' };
function entidadHTML(f, conInterruptor) {
  const docs = (f.documentos || []).map(d => `<li>PDF: ${esc(d)}</li>`).join('');
  const api = f.metodo === 'api' || f.id ? `<li>${esc(f.descripcion || 'Conexión por API')}</li>` : '';
  const tog = f.id ? (conInterruptor === 'wz'
      ? `<input type="checkbox" data-wz-broker="${esc(f.id)}" ${f.activo ? 'checked' : ''}>`
      : `<label class="interruptor"><input type="checkbox" data-cfg="brokers.${esc(f.id)}.activo"><span></span></label>`)
    : '<span class="empty" style="font-size:12px">por PDF</span>';
  return `<div class="entidad"><div class="cab"><b>${esc(f.nombre)}<span class="tipo">${esc(TIPOS[f.tipo] || f.tipo)}</span></b>${tog}</div><ul>${docs}${api}</ul></div>`;
}
let dinamicaArmada = false;
function armarConfigDinamica() {
  if (dinamicaArmada) return;
  dinamicaArmada = true;
  $('#cfg-entidades').innerHTML = EST.fuentes.map(f => entidadHTML(f)).join('');
  $('#sel-proveedor').innerHTML = EST.proveedores_ia.map(p => `<option value="${esc(p.id)}">${esc(p.nombre)}</option>`).join('');
  $('#cfg-proveedores').innerHTML = EST.proveedores_ia.map(p => `<div data-prov="${esc(p.id)}" hidden>
    <div class="campo"><label>Modelo</label><input type="text" data-cfg="analisis.${esc(p.id)}.modelo" placeholder="${esc(p.modelo || 'el predeterminado')}"></div>
    ${p.usa_url ? `<div class="campo"><label>Dirección del servidor</label><input type="text" data-cfg="analisis.${esc(p.id)}.url"></div>` : ''}
    ${p.secreto ? `<div class="campo"><label>Clave de API</label><div class="secreto" data-secreto="${esc(p.secreto)}"></div></div>` : ''}
  </div>`).join('');
  $('#sel-proveedor').onchange = mostrarProveedor;
}
function mostrarProveedor() {
  const id = $('#sel-proveedor').value, p = EST.proveedores_ia.find(x => x.id === id);
  $$('[data-prov]').forEach(d => d.hidden = d.dataset.prov !== id);
  $('#ayuda-proveedor').textContent = p ? p.descripcion : '';
}
$('#btn-probar-ia').onclick = async () => {
  await API.guardar_config(leerConfig());
  $('#msg-probar-ia').className = 'msg'; $('#msg-probar-ia').textContent = 'Probando…';
  const r = await API.probar_ia();
  $('#msg-probar-ia').className = 'msg ' + (r.ok ? 'ok' : 'err'); $('#msg-probar-ia').textContent = (r.ok ? '✓ ' : '✗ ') + r.mensaje;
};

// ---------- asistente de bienvenida ----------
let wzPaso = 1;
function abrirBienvenida() {
  const c = EST.config;
  $('#wz-reportes').value = c.fuentes.reportes; $('#wz-descargas').value = c.fuentes.descargas;
  $('#wz-fuentes').innerHTML = EST.fuentes.map(f => entidadHTML(f, 'wz')).join('');
  $('#wz-ia').innerHTML = EST.proveedores_ia.map(p => `<label class="opcion"><input type="radio" name="wz-prov" value="${esc(p.id)}" ${p.id === c.analisis.proveedor ? 'checked' : ''}>
    <div><b>${esc(p.nombre)}</b><div class="d">${esc(p.descripcion)}</div></div></label>`).join('');
  $$('[name="wz-prov"]').forEach(r => r.onchange = wzProveedor);
  wzProveedor();
  $$('[data-wz-elegir]').forEach(b => b.onclick = async () => { const r = await API.elegir_carpeta(); if (r) $('#' + b.dataset.wzElegir).value = r; });
  wzIr(1);
  $('#bienvenida').hidden = false;
}
function wzProveedor() {
  const id = ($('[name="wz-prov"]:checked') || {}).value, p = EST.proveedores_ia.find(x => x.id === id) || {};
  $('#wz-modelo').value = EST.config.analisis[id]?.modelo || p.modelo || '';
  $('#wz-modelo').placeholder = p.modelo || 'el predeterminado';
  $('#wz-clave-box').hidden = !p.secreto;
  $('#wz-clave').value = '';
}
function wzIr(n) {
  wzPaso = n;
  $$('#bienvenida [data-paso]').forEach(sec => sec.hidden = +sec.dataset.paso !== n);
  $('#wz-pasos').innerHTML = [1, 2, 3, 4].map(i => `<span class="${i <= n ? 'on' : ''}"></span>`).join('');
  $('#wz-atras').hidden = n === 1;
  $('#wz-siguiente').textContent = n === 4 ? 'Empezar' : 'Siguiente';
  $('#wz-error').textContent = '';
  if (n === 4) {
    const brokers = $$('[data-wz-broker]').filter(x => x.checked).map(x => EST.fuentes.find(f => f.id === x.dataset.wzBroker).nombre);
    const prov = EST.proveedores_ia.find(x => x.id === ($('[name="wz-prov"]:checked') || {}).value);
    $('#wz-resumen').innerHTML = `<ul class="obs" style="color:var(--text-2)"><li>Resúmenes en <b>${esc($('#wz-reportes').value)}</b></li>
      <li>Brokers en vivo: <b>${esc(brokers.join(', ') || 'ninguno')}</b></li><li>IA: <b>${esc(prov ? prov.nombre : '—')}</b></li></ul>`;
  }
}
$('#wz-atras').onclick = () => wzIr(Math.max(1, wzPaso - 1));
$('#wz-saltar').onclick = async () => { await API.guardar_config({}); $('#bienvenida').hidden = true; await refrescar(); };
$('#wz-siguiente').onclick = async () => {
  if (wzPaso === 1 && !$('#wz-reportes').value.trim()) { $('#wz-error').textContent = 'Elegí una carpeta para los resúmenes'; return; }
  if (wzPaso < 4) return wzIr(wzPaso + 1);
  const prov = ($('[name="wz-prov"]:checked') || {}).value || 'claude_code';
  const p = EST.proveedores_ia.find(x => x.id === prov);
  const brokers = {};
  $$('[data-wz-broker]').forEach(x => brokers[x.dataset.wzBroker] = { activo: x.checked });
  await API.guardar_config({
    fuentes: { reportes: $('#wz-reportes').value.trim(), descargas: $('#wz-descargas').value.trim(), importar_descargas: true },
    brokers, analisis: { activado: true, proveedor: prov, [prov]: { modelo: $('#wz-modelo').value.trim() } },
  });
  const clave = $('#wz-clave').value; $('#wz-clave').value = '';
  if (p && p.secreto && clave) {
    const r = await API.guardar_secreto(p.secreto, clave);
    if (!r.ok) { $('#wz-error').textContent = 'No pude guardar la clave: ' + r.error + '. Podés cargarla después en Configuración.'; }
  }
  $('#bienvenida').hidden = true;
  dinamicaArmada = false;
  await refrescar();
};
$('#btn-asistente').onclick = abrirBienvenida;

// ---------- configuración ----------
const get = (o, path) => path.split('.').reduce((a, k) => a?.[k], o);
const set = (o, path, v) => { const ks = path.split('.'); ks.slice(0, -1).reduce((a, k) => a[k] = a[k] || {}, o)[ks.at(-1)] = v; };
function llenarConfig(c) {
  $$('[data-cfg]').forEach(el => {
    const v = get(c, el.dataset.cfg);
    if (el.type === 'checkbox') el.checked = !!v;
    else if (el.hasAttribute('data-pct')) el.value = v ? +(v * 100).toFixed(2) : 0;
    else if (el.hasAttribute('data-lista')) el.value = (v || []).join(', ');
    else el.value = v ?? '';
  });
  mostrarDestino();
  mostrarProveedor();
}
function leerConfig() {
  const c = {};
  $$('[data-cfg]').forEach(el => {
    let v = el.type === 'checkbox' ? el.checked : el.value.trim();
    if (el.hasAttribute('data-pct')) v = (parseFloat(v) || 0) / 100;
    if (el.hasAttribute('data-num')) v = parseInt(v, 10) || 0;
    if (el.hasAttribute('data-lista')) v = v.split(/[,;\s]+/).map(x => x.trim().toUpperCase()).filter(Boolean);
    set(c, el.dataset.cfg, v);
  });
  return c;
}
function mostrarDestino() {
  const d = $('[data-cfg="publicar.destino"]').value;
  $('#cfg-github').hidden = d !== 'github';
  $('#cfg-drive').hidden = d !== 'drive';
  $('[data-secreto="celular_password"]').closest('.campo').hidden = d === 'ninguno';
}
$('[data-cfg="publicar.destino"]').onchange = mostrarDestino;
$('#btn-guardar').onclick = async () => {
  const c = leerConfig();
  if (c.publicar.destino === 'github' && c.publicar.github.repo && !/^[\w.-]+\/[\w.-]+$/.test(c.publicar.github.repo)) {
    $('#msg-guardar').className = 'msg err'; $('#msg-guardar').textContent = 'El repositorio tiene que ser usuario/repo'; return;
  }
  const tarjetas = leerTarjetas();
  if (tarjetas.error) { $('#msg-guardar').className = 'msg err'; $('#msg-guardar').textContent = tarjetas.error; return; }
  const objetivos = leerObjetivos();
  if (objetivos.error) { $('#msg-guardar').className = 'msg err'; $('#msg-guardar').textContent = objetivos.error; return; }
  await API.guardar_config(c);
  await API.reemplazar_config('presupuestos', leerLimites());
  await API.reemplazar_config('tarjetas', tarjetas.valor);
  await API.reemplazar_config('objetivos', objetivos.valor);
  $('#msg-guardar').className = 'msg ok'; $('#msg-guardar').textContent = '✓ Guardado';
  setTimeout(() => $('#msg-guardar').textContent = '', 2500);
  await refrescar();
};
$$('[data-elegir]').forEach(b => b.onclick = async () => { const r = await API.elegir_carpeta(); if (r) $(`[data-cfg="${b.dataset.elegir}"]`).value = r; });
$('#btn-elegir-secret').onclick = async () => { const r = await API.elegir_archivo(); if (r) $('[data-cfg="publicar.drive.client_secret"]').value = r; };
$('#btn-probar').onclick = async () => {
  await API.guardar_config(leerConfig());
  $('#msg-probar').className = 'msg'; $('#msg-probar').textContent = 'Probando…';
  const r = await API.probar_github();
  $('#msg-probar').className = 'msg ' + (r.ok ? 'ok' : 'err'); $('#msg-probar').textContent = (r.ok ? '✓ ' : '✗ ') + r.mensaje;
};

// ---------- secretos ----------
let secActual = null;
function pintarSecretos() {
  $$('[data-secreto]').forEach(el => {
    const n = el.dataset.secreto, s = EST.secretos[n];
    el.innerHTML = `<span class="badge ${s.guardado ? 'ok' : ''}">${s.guardado ? '✓ Guardado en el llavero' : 'No guardado'}</span>
      <button class="btn" data-accion="cambiar" ${EST.llavero.ok ? '' : 'disabled'}>${s.guardado ? 'Cambiar' : 'Guardar'}</button>
      ${s.guardado ? '<button class="btn peligro" data-accion="borrar">Borrar</button>' : ''}`;
    el.querySelector('[data-accion="cambiar"]').onclick = () => abrirSecreto(n);
    const b = el.querySelector('[data-accion="borrar"]');
    if (b) b.onclick = async () => { if (confirm('¿Borrar del llavero?')) { await API.borrar_secreto(n); await refrescar(); } };
  });
}
function abrirSecreto(n) {
  secActual = n;
  $('#sec-titulo').textContent = EST.secretos[n].descripcion;
  $('#sec-valor').value = ''; $('#sec-repetir').value = ''; $('#sec-error').textContent = '';
  $('#sec-valor').placeholder = n === 'github_token' ? 'github_pat_…' : 'Contraseña (mínimo 12 caracteres)';
  $('#sec-repetir').hidden = n !== 'celular_password';
  $('#modal-secreto').hidden = false; $('#sec-valor').focus();
}
$('#sec-cancelar').onclick = () => { $('#sec-valor').value = ''; $('#sec-repetir').value = ''; $('#modal-secreto').hidden = true; };
$('#form-secreto').onsubmit = async e => {
  e.preventDefault();
  const v = $('#sec-valor').value;
  if (secActual === 'celular_password' && v !== $('#sec-repetir').value) { $('#sec-error').textContent = 'No coinciden'; return; }
  const r = await API.guardar_secreto(secActual, v);
  $('#sec-valor').value = ''; $('#sec-repetir').value = '';
  if (!r.ok) { $('#sec-error').textContent = r.error; return; }
  $('#modal-secreto').hidden = true;
  await refrescar();
};
document.addEventListener('keydown', e => { if (e.key === 'Escape') $$('.fondo-modal').forEach(m => m.hidden = true); });

// ---------- arranque ----------
window.addEventListener('pywebviewready', async () => { API = window.pywebview.api; await refrescar(); ir('inicio'); });
