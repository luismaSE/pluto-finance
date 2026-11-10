const DATA = /*__DATOS__*/null;
const S = DATA.snapshot, R = DATA.resumen;
const HOY = DATA.hoy || new Date().toISOString().slice(0, 10);

// ---------- formato ----------
const nf0 = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 0 });
const nf2 = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
const nf1 = new Intl.NumberFormat('es-AR', { minimumFractionDigits: 1, maximumFractionDigits: 1 });
const money = (n, m = 'ARS', dec = false) => n == null ? '—' : (n < 0 ? '−' : '') + (m === 'USD' ? 'US$ ' : '$ ') + (dec ? nf2 : nf0).format(Math.abs(n));
const compact = (n, m = 'ARS') => {
  if (n == null) return '—';
  const a = Math.abs(n), s = (n < 0 ? '−' : '') + (m === 'USD' ? 'US$ ' : '$ ');
  if (a >= 1e6) return s + nf2.format(a / 1e6).replace(/,00$/, '') + ' M';
  if (a >= 1e4) return s + nf0.format(a / 1e3) + ' k';
  return s + nf0.format(a);
};
const pct = (n, signo = true) => n == null || !isFinite(n) ? '—' : (signo && n > 0 ? '+' : '') + nf1.format(n) + '%';
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const M = s => `<span class="m">${s}</span>`;     // monto (se oculta en modo privado)
const dm = iso => iso ? iso.slice(8, 10) + '/' + iso.slice(5, 7) : '?';
const dias = iso => iso ? Math.round((new Date(HOY) - new Date(iso)) / 864e5) : null;
const nombreMes = (mes, corto) => { const [y, m] = mes.split('-').map(Number); return new Date(y, m - 1, 1).toLocaleDateString('es-AR', corto ? { month: 'short' } : { month: 'long', year: 'numeric' }); };
const finMes = mes => { const [y, m] = mes.split('-').map(Number); return `${mes}-${String(new Date(y, m, 0).getDate()).padStart(2, '0')}`; };
// Color fijo por entidad, en el orden del catálogo de fuentes (nunca por ranking)
const PALETA_ENT = ['var(--s2)', 'var(--s1)', 'var(--s3)', 'var(--s4)', 'var(--s5)'];
const ENT_COLOR = {};
(DATA.entidades || ['Galicia', 'Mercado Pago', 'IOL']).forEach((e, i) => ENT_COLOR[e] = PALETA_ENT[i] || 'var(--text-3)');
const entColor = e => ENT_COLOR[e] || 'var(--text-3)';
const tipoBonito = t => String(t || '').replace('TITULOSPUBLICOS', 'Títulos públicos').replace('CEDEARS', 'CEDEARs').replace('ACCIONES', 'Acciones').replace('PLAZO FIJO', 'Plazo fijo');
const store = { get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } }, set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} } };

// ---------- datos derivados ----------
const MESES = Object.keys(R.gastos_por_mes).sort();
const EXCL = new Set(R.categorias_excluidas || []);
const ENTIDADES_PDF = [...new Set((R.cobertura || []).map(c => c.entidad))];

function coberturaMes(mes) {
  const ini = mes + '-01', fin = finMes(mes);
  return (R.cobertura || []).map(c => {
    const d = c.desde > ini ? c.desde : ini, h = c.hasta < fin ? c.hasta : fin;
    return d <= h ? { ...c, d, h, completo: d === ini && h === fin, dias: (new Date(h) - new Date(d)) / 864e5 + 1 } : { ...c, d: null, dias: 0 };
  });
}
// Entidades con datos en el mes y cuántos días cubre la mejor cuenta de cada una
function calidadMes(mes) {
  const por = {};
  coberturaMes(mes).forEach(c => { por[c.entidad] = Math.max(por[c.entidad] || 0, c.dias); });
  const con = Object.entries(por).filter(([, d]) => d > 0).map(([e]) => e);
  return { con, sin: ENTIDADES_PDF.filter(e => !con.includes(e)), dias: Object.values(por).reduce((a, b) => a + b, 0) };
}
// Mes de referencia: el más reciente con más días cubiertos
const MES_REF = MESES.slice().sort((a, b) => calidadMes(b).con.length - calidadMes(a).con.length
  || calidadMes(b).dias - calidadMes(a).dias || (a < b ? 1 : -1))[0] || null;

// Gasto mensual típico: promedio de meses con al menos 20 días de datos
function gastoMensualTipico() {
  // Cada resumen cubre meses distintos: se promedia el gasto de cada entidad en sus meses
  // con al menos 20 días de datos, y después se suman las entidades.
  let total = 0, alguno = false;
  ENTIDADES_PDF.forEach(e => {
    const vals = MESES.filter(m => coberturaMes(m).some(c => c.entidad === e && c.dias >= 20))
      .map(m => R.gastos_por_mes[m].por_entidad[e] || 0);
    if (vals.length) { total += vals.reduce((a, b) => a + b, 0) / vals.length; alguno = true; }
  });
  if (alguno) return total;
  const lista = MESES.map(m => R.gastos_por_mes[m].total_ars).filter(v => v > 0);
  return lista.length ? lista.reduce((a, b) => a + b, 0) / lista.length : null;
}

// ---------- componentes ----------
function hbars(rows, { color, fmt = compact, total } = {}) {
  if (!rows.length) return '<div class="empty">Sin datos</div>';
  const max = Math.max(...rows.map(r => r.v), 1);
  return '<div class="hbars">' + rows.map(r => {
    const share = total ? ` · ${nf1.format(r.v / total * 100)}%` : '';
    const c = typeof color === 'function' ? color(r) : color;
    return `<div class="hbar" data-tip="${esc(`<b>${esc(r.k)}</b><br>${esc(fmt(r.v))}${share}`)}">
      <div class="name">${r.dot ? `<span class="dot" style="background:${c}"></span>` : ''}${esc(r.k)}</div>
      <div class="track"><div class="fill" style="width:${(r.v / max * 100).toFixed(2)}%;background:${c}"></div></div>
      <div class="val">${M(esc(fmt(r.v)))}</div></div>`;
  }).join('') + '</div>';
}

// Tinta legible sobre cada color de fondo: oscura sobre amarillo y naranja claro, blanca sobre el resto
const tinta = c => /warning|serious/.test(c) ? '#241a00' : '#fff';
const NIVEL = { alta: ['var(--critical)', '!', 0], media: ['var(--serious)', '!', 1], baja: ['var(--warning)', 'i', 2] };
function alertasHTML(alertas, max) {
  if (!alertas?.length) return '<div class="empty">Sin alertas.</div>';
  const orden = alertas.slice().sort((a, b) => (NIVEL[a.nivel] || NIVEL.baja)[2] - (NIVEL[b.nivel] || NIVEL.baja)[2]);
  return orden.slice(0, max || orden.length).map(a => {
    const [c, i] = NIVEL[a.nivel] || NIVEL.baja;
    return `<div class="alert"><div class="ico" style="background:${c};color:${tinta(c)}">${i}</div>
      <div><div class="t">${esc(a.titulo)}<span class="lvl">${esc(a.nivel)}</span></div><div class="d">${esc(a.detalle)}</div></div></div>`;
  }).join('');
}

function avisosDatosViejos() {
  const items = [];
  const porEntidad = {};
  [...R.liquidez, ...R.inversiones].forEach(x => {
    const d = dias(x.al);
    if (d != null && (porEntidad[x.entidad] == null || d < porEntidad[x.entidad].d)) porEntidad[x.entidad] = { d, al: x.al };
  });
  Object.entries(porEntidad).forEach(([e, { d, al }]) => {
    if (d > 20) items.push(`<div class="aviso">⏱ <div><b>${esc(e)}</b>: datos al ${dm(al)} (hace ${d} días). Descargá el resumen nuevo.</div></div>`);
  });
  Object.entries(S.estado_fuentes || {}).forEach(([k, v]) => {
    if (!v.ok) items.push(`<div class="aviso" style="border-left-color:var(--critical)">✕ <div><b>${esc(k)}</b>: ${esc(v.detalle)}</div></div>`);
  });
  (S.advertencias || []).forEach(a => items.push(`<div class="aviso">⚠ <div>${esc(a)}</div></div>`));
  return items.join('');
}

// Evolución del patrimonio (un punto por día con corrida)
function lineaPatrimonio() {
  const H0 = (DATA.historial || []).filter(x => x.patrimonio_ars);
  if (H0.length < 2) return `<div class="empty">Se va completando con cada actualización (${H0.length} de 2 corridas como mínimo).</div>`;
  const angosto = innerWidth < 600;
  const W = angosto ? 360 : 720, H = 170, pl = angosto ? 40 : 48, pr = 10, pt = 10, pb = 22;
  const vals = H0.map(x => x.patrimonio_ars);
  let lo = Math.min(...vals), hi = Math.max(...vals);
  const pad = (hi - lo) * 0.15 || hi * 0.05; lo = Math.max(0, lo - pad); hi = hi + pad;
  const xv = i => pl + (W - pl - pr) * (H0.length === 1 ? 0.5 : i / (H0.length - 1));
  const yv = v => pt + (H - pt - pb) * (1 - (v - lo) / (hi - lo));
  let g = '';
  for (let i = 0; i <= 3; i++) {
    const v = lo + (hi - lo) * i / 3, yy = yv(v);
    g += `<line x1="${pl}" x2="${W - pr}" y1="${yy}" y2="${yy}" stroke="var(--grid)"/><text class="m" x="${pl - 6}" y="${yy + 4}" text-anchor="end">${compact(v).replace('$ ', '')}</text>`;
  }
  g += `<path d="${H0.map((x, i) => (i ? 'L' : 'M') + xv(i).toFixed(1) + ',' + yv(x.patrimonio_ars).toFixed(1)).join(' ')}" fill="none" stroke="var(--seq)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>`;
  const paso = Math.max(1, Math.ceil(H0.length / (angosto ? 4 : 8)));
  H0.forEach((x, i) => {
    const cx = xv(i), cy = yv(x.patrimonio_ars);
    if (i === H0.length - 1) g += `<circle cx="${cx}" cy="${cy}" r="4.5" fill="var(--seq)" stroke="var(--surface)" stroke-width="2"/>`;
    g += `<circle cx="${cx}" cy="${cy}" r="12" fill="transparent" data-tip="${esc(`<b>${dm(x.fecha.slice(0, 10))}</b><br>${compact(x.patrimonio_ars)}${x.patrimonio_usd ? ' · ' + money(x.patrimonio_usd, 'USD') : ''}`)}"/>`;
    const anc = i === 0 ? 'start' : i === H0.length - 1 ? 'end' : 'middle';
    if (i % paso === 0 || i === H0.length - 1) g += `<text x="${cx}" y="${H - 5}" text-anchor="${anc}">${dm(x.fecha.slice(0, 10))}</text>`;
  });
  const prim = H0[0].patrimonio_ars, ult = H0[H0.length - 1].patrimonio_ars, d = (ult - prim) / prim * 100;
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Evolución del patrimonio">${g}</svg>
    <p class="nota">Desde el ${dm(H0[0].fecha.slice(0, 10))}: <b class="${d >= 0 ? 'pos' : 'neg'}">${pct(d)}</b> en pesos${H0[0].patrimonio_usd && H0[H0.length - 1].patrimonio_usd ? ` · ${pct((H0[H0.length - 1].patrimonio_usd - H0[0].patrimonio_usd) / H0[0].patrimonio_usd * 100)} en dólares` : ''}.</p>`;
}

// Cuánto cuesta tener pesos quietos
function plataQuieta() {
  const ref = DATA.referencias || {};
  const pesos = R.pesos_liquidos_ars || 0;
  if (!pesos || (!ref.tna_plazo_fijo && !ref.inflacion_mensual)) return '';
  const gan = ref.tna_plazo_fijo ? pesos * ref.tna_plazo_fijo / 12 : null;
  const inf = ref.inflacion_mensual ? pesos * ref.inflacion_mensual : null;
  const usd = R.liquidez.filter(c => c.moneda === 'USD').reduce((a, c) => a + c.saldo, 0);
  return `<div class="card c6"><h2>Plata quieta</h2>
    <div class="trio" style="grid-template-columns:repeat(${gan != null && inf != null ? 2 : 1},1fr)">
      ${inf != null ? `<div class="kpi"><div class="label">Pierde por inflación</div><div class="value neg">${M(compact(inf))}<span style="font-size:13px;font-weight:500"> /mes</span></div>
        <div class="note">${nf1.format(ref.inflacion_mensual * 100)}% mensual (${esc(ref.inflacion_mes || '')})</div></div>` : ''}
      ${gan != null ? `<div class="kpi"><div class="label">Ganaría a plazo fijo</div><div class="value pos">${M(compact(gan))}<span style="font-size:13px;font-weight:500"> /mes</span></div>
        <div class="note">TNA ${nf1.format(ref.tna_plazo_fijo * 100)}%</div></div>` : ''}
    </div>
    <p class="nota">Sobre tus ${M(compact(pesos))} en pesos en cuentas.${usd > 0 ? ` Además tenés ${M(money(usd, 'USD'))} en cuentas sin invertir.` : ''}${ref.tna_fuente ? ' Tasa: ' + esc(ref.tna_fuente) + '.' : ''}</p></div>`;
}

// Ingresos vs gastos por mes (barras agrupadas)
function flujoMeses() {
  if (!MESES.length) return '<div class="empty">Sin datos</div>';
  const angosto = innerWidth < 600;
  const meses = MESES.slice(angosto ? -4 : -8);
  const W = angosto ? 360 : 720, H = 180, pl = angosto ? 40 : 48, pr = 6, pt = 8, pb = 24;
  const max = Math.max(1, ...meses.flatMap(m => [R.gastos_por_mes[m].total_ars, R.gastos_por_mes[m].ingresos_ars]));
  const nice = (() => { const p = Math.pow(10, Math.floor(Math.log10(max))); return Math.ceil(max / p) * p; })();
  const gw = (W - pl - pr) / meses.length, bw = Math.min(28, gw * 0.32), yv = v => pt + (H - pt - pb) * (1 - v / nice);
  let g = '';
  for (let i = 0; i <= 3; i++) {
    const v = nice * i / 3, yy = yv(v);
    g += `<line x1="${pl}" x2="${W - pr}" y1="${yy}" y2="${yy}" stroke="var(--grid)"/><text class="m" x="${pl - 6}" y="${yy + 4}" text-anchor="end">${compact(v).replace('$ ', '')}</text>`;
  }
  const barra = (x, v, color) => { const yy = yv(v), h = H - pb - yy, r = Math.min(4, bw / 2, h);
    return v > 0 ? `<path d="M${x},${H - pb} V${yy + r} q0,-${r} ${r},-${r} h${bw - 2 * r} q${r},0 ${r},${r} V${H - pb} Z" fill="${color}"/>` : ''; };
  meses.forEach((m, i) => {
    const G = R.gastos_por_mes[m], cx = pl + gw * i + gw / 2, parcial = calidadMes(m).sin.length > 0;
    g += barra(cx - bw - 1, G.ingresos_ars, 'var(--s3)') + barra(cx + 1, G.total_ars, 'var(--s2)');
    g += `<rect x="${cx - gw / 2}" y="${pt}" width="${gw}" height="${H - pt - pb}" fill="transparent" data-tip="${esc(`<b>${nombreMes(m)}</b>${parcial ? ' (parcial)' : ''}<br>Ingresos ${compact(G.ingresos_ars)}<br>Gastos ${compact(G.total_ars)}`)}"/>`;
    g += `<text x="${cx}" y="${H - 6}" text-anchor="middle">${esc(nombreMes(m, true))}${parcial ? '*' : ''}</text>`;
  });
  g += `<line x1="${pl}" x2="${W - pr}" y1="${H - pb}" y2="${H - pb}" stroke="var(--border)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Ingresos y gastos por mes">${g}</svg>
    <div class="legend" style="margin-top:6px"><span><i class="dot" style="background:var(--s3)"></i>Ingresos</span><span><i class="dot" style="background:var(--s2)"></i>Gastos</span><span class="muted">* mes con datos incompletos</span></div>`;
}

// Suscripciones y gastos que se repiten todos los meses
function gastosFijos() {
  const norm = d => d.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/\d{4,}/g, '').replace(/\s+/g, ' ').trim();
  const grupos = {};
  S.movimientos.filter(m => m.monto < 0 && !EXCL.has(m.categoria) && m.categoria !== 'Pago de tarjeta').forEach(m => {
    const k = norm(m.descripcion); (grupos[k] = grupos[k] || []).push(m);
  });
  const fijos = [];
  Object.values(grupos).forEach(ms => {
    const porMes = {};
    ms.forEach(m => { porMes[m.fecha.slice(0, 7)] = (porMes[m.fecha.slice(0, 7)] || 0) + -m.monto * (m.moneda === 'USD' ? (R.tipo_cambio_mep || 0) : 1); });
    const vals = Object.values(porMes), prom = vals.reduce((a, b) => a + b, 0) / vals.length;
    const parecidos = vals.every(v => Math.abs(v - prom) <= prom * 0.2);
    const esSusc = ms[0].categoria === 'Suscripciones';
    if ((vals.length >= 2 && parecidos) || esSusc) fijos.push({ desc: ms[0].descripcion, cat: ms[0].categoria, mensual: prom, meses: vals.length, entidad: ms[0].entidad });
  });
  fijos.sort((a, b) => b.mensual - a.mensual);
  if (!fijos.length) return '<div class="empty">Todavía no detecté gastos que se repitan (hacen falta al menos 2 meses de resúmenes).</div>';
  const total = fijos.reduce((a, f) => a + f.mensual, 0);
  return `<div class="lista">${fijos.slice(0, 10).map(f => `<div class="fila">
      <div class="t">${esc(f.desc)}</div><div class="v">${M(compact(f.mensual))}<span class="muted" style="font-weight:400">/mes</span></div>
      <div class="d">${esc(f.cat)} · ${esc(f.entidad)} · ${f.meses >= 2 ? `se repite ${f.meses} meses` : 'suscripción'}</div><div class="v2">${M(compact(f.mensual * 12))}/año</div></div>`).join('')}</div>
    <p class="nota">Total estimado: ${M(`<b>${compact(total)}</b>`)} por mes · ${M(compact(total * 12))} por año.</p>`;
}

// ---------- pestaña: Resumen ----------
// ---------- tarjetas, límites de gasto y avisos ----------
const HOY0 = (() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d; })();
const isoAFecha = iso => { const [y, m, d] = iso.split('-').map(Number); return new Date(y, m - 1, d); };
// Próxima fecha con ese día del mes (hoy incluido); 31 en meses cortos = último día
function proximaFecha(dia) {
  const f = (y, m) => new Date(y, m, Math.min(dia, new Date(y, m + 1, 0).getDate()));
  let d = f(HOY0.getFullYear(), HOY0.getMonth());
  if (d < HOY0) d = f(HOY0.getFullYear(), HOY0.getMonth() + 1);
  return d;
}
// Si el dashboard se abre días después de generarse, recalcula con la fecha de hoy
function fechaTarjeta(iso, dia) {
  let d = iso ? isoAFecha(iso) : null;
  if ((!d || d < HOY0) && dia) d = proximaFecha(dia);
  return d && d >= HOY0 ? d : null;
}
const diasHasta = d => Math.round((d - HOY0) / 864e5);
const cuandoTxt = n => n === 0 ? 'hoy' : n === 1 ? 'mañana' : `en ${n} días`;
const ddmm = d => String(d.getDate()).padStart(2, '0') + '/' + String(d.getMonth() + 1).padStart(2, '0');
const URG = n => n <= 3 ? ['var(--critical)', 'Urgente'] : n <= 7 ? ['var(--warning)', 'Pronto'] : ['var(--good)', 'Tranquilo'];

function tarjetasHTML() {
  const T = R.tarjetas || [];
  if (!T.length) return '';
  const fila = (t) => {
    const c = fechaTarjeta(t.proximo_cierre, t.cierre_dia), v = fechaTarjeta(t.proximo_vencimiento, t.vencimiento_dia);
    const chip = (etq, d) => {
      if (!d) return `<span class="chip-t muted">${etq}: sin fecha</span>`;
      const n = diasHasta(d), [col, txt] = URG(n);
      return `<span class="chip-t"><i style="background:${col}" title="${txt}"></i>${etq} ${cuandoTxt(n)} <span class="muted">· ${ddmm(d)}</span></span>`;
    };
    const up = t.ultimo_pago ? `Último pago: ${M(money(t.ultimo_pago.monto, t.ultimo_pago.moneda))} el ${dm(t.ultimo_pago.fecha)}` : '';
    return `<div class="tarjeta-f"><div class="t">${esc(t.nombre)}</div><div class="chips-t">${chip('Cierra', c)}${chip('Vence', v)}</div>${up ? `<div class="d">${up}</div>` : ''}</div>`;
  };
  return `<div class="card c6"><h2>Tarjetas</h2>${T.map(fila).join('')}
    <p class="nota">Los bancos corren las fechas unos días algunos meses: si tu resumen dice otra, cargala en la app.</p></div>`;
}

// Avisos de tarjetas y límites, recalculados para la fecha de hoy
function avisosPlan() {
  const out = [];
  (R.tarjetas || []).forEach(t => {
    const v = fechaTarjeta(t.proximo_vencimiento, t.vencimiento_dia), c = fechaTarjeta(t.proximo_cierre, t.cierre_dia);
    if (v && diasHasta(v) <= 7) out.push({ nivel: diasHasta(v) <= 3 ? 'alta' : 'media', titulo: `${t.nombre} vence ${cuandoTxt(diasHasta(v))}`, detalle: `Vencimiento el ${ddmm(v)}.` });
    if (c && diasHasta(c) <= 3) out.push({ nivel: 'baja', titulo: `${t.nombre} cierra ${cuandoTxt(diasHasta(c))}`, detalle: 'Lo que compres después del cierre entra en el resumen siguiente.' });
  });
  (R.avisos || []).filter(a => a.tipo === 'presupuesto').forEach(a => out.push(a));
  return out;
}

const ESTADO_LIM = { ok: ['var(--good)', 'En línea'], cerca: ['var(--warning)', 'Cerca'], excedido: ['var(--critical)', 'Excedido'] };
function limitesHTML(mes) {
  const P = R.presupuestos || {};
  if (!P.configurado) return `<div class="card"><h2>Límites de gasto</h2><div class="empty">Todavía no configuraste límites. En la app de escritorio: Configuración → Límites de gasto.</div></div>`;
  const pm = (P.meses || {})[mes];
  if (!pm) return '';
  const fila = it => {
    const [col, txt] = ESTADO_LIM[it.estado] || ESTADO_LIM.ok, w = Math.min(it.pct, 100);
    const proy = it.proyeccion ? ` · a este ritmo: ${M(compact(it.proyeccion))}` : '';
    return `<div class="lim">
      <div class="lim-cab"><b>${esc(it.nombre)}</b><span class="estado-l"><i style="background:${col}"></i>${txt} · ${nf0.format(it.pct)}%</span></div>
      <div class="lim-barra" data-tip="${esc(`<b>${esc(it.nombre)}</b><br>${compact(it.gastado)} de ${compact(it.limite)}`)}"><div style="width:${w.toFixed(1)}%;background:${it.estado === 'ok' ? 'var(--seq)' : col}"></div></div>
      <div class="d">${M(compact(it.gastado))} de ${M(compact(it.limite))} · ${it.restante >= 0 ? 'quedan ' + M(compact(it.restante)) : 'excedido por ' + M(compact(-it.restante))}${proy}</div></div>`;
  };
  const items = (pm.total ? [pm.total] : []).concat(pm.categorias || []);
  return `<div class="card"><h2>Límites de gasto · ${esc(nombreMes(mes))}</h2><div class="lims">${items.map(fila).join('')}</div>
    ${calidadMes(mes).sin.length ? '<p class="nota">Mes con datos incompletos: el gasto real puede ser mayor.</p>' : ''}</div>`;
}

function renderResumen() {
  const tc = R.tipo_cambio_mep;
  const enCuentas = R.liquidez_ars, total = R.patrimonio_ars || 0;
  const gtipico = gastoMensualTipico();
  const meses = gtipico ? enCuentas / gtipico : null;
  const meta = (R.metas || {}).fondo_emergencia_meses || 0;
  const G = MES_REF ? R.gastos_por_mes[MES_REF] : null;
  const ahorro = G ? G.ingresos_ars - G.total_ars : null;
  const tasa = G && G.ingresos_ars ? ahorro / G.ingresos_ars * 100 : null;
  const q = MES_REF ? calidadMes(MES_REF) : { con: [], sin: [] };
  const parcial = q.sin.length ? `falta el resumen de ${q.sin.join(' y ')}` : '';
  const pctCuentas = total ? enCuentas / total * 100 : 0;
  const A = S.analisis && !S.analisis.error ? S.analisis : null;

  let frase = '';
  if (G && !parcial) frase += `En <b>${esc(nombreMes(MES_REF))}</b> entraron ${M(`<b>${compact(G.ingresos_ars)}</b>`)} y gastaste ${M(`<b>${compact(G.total_ars)}</b>`)}${tasa != null && tasa > 0 ? `: ahorraste el <b>${nf0.format(tasa)}%</b>` : ''}. `;
  else if (G) frase += `En <b>${esc(nombreMes(MES_REF))}</b> gastaste ${M(`<b>${compact(G.total_ars)}</b>`)} por ${esc(q.con.join(' y '))} <span class="muted">(${esc(parcial)} de ese mes)</span>. `;
  if (pctCuentas > 25) frase += `El <b>${nf0.format(pctCuentas)}%</b> de tu plata está en cuentas, sin invertir.`;

  const ents = Object.entries(R.por_entidad).map(([k, v]) => ({ k, v, dot: true }));
  const pm = R.por_moneda, pmTot = (pm.ARS || 0) + (pm.USD || 0);

  document.getElementById('p-resumen').innerHTML = `<div class="grid">
    ${avisosDatosViejos()}
    ${avisosPlan().map(a => `<div class="aviso" style="border-left-color:${(NIVEL[a.nivel] || NIVEL.baja)[0]}">${a.nivel === 'alta' ? '⚠' : '•'} <div><b>${esc(a.titulo)}</b> ${esc(a.detalle)}</div></div>`).join('')}
    <div class="card hero">
      <div class="kpi"><div class="label">Patrimonio total</div></div>
      <div class="total">${M(compact(total))}${R.patrimonio_usd ? `<small>${M('≈ ' + money(R.patrimonio_usd, 'USD'))}</small>` : ''}</div>
      ${frase ? `<p>${frase}</p>` : ''}
    </div>
    <div class="card kpi c3"><div class="label">Ahorro · ${esc(MES_REF ? nombreMes(MES_REF, true) : '—')}</div>
      ${parcial ? `<div class="value muted">Incompleto</div><div class="note">${esc(parcial[0].toUpperCase() + parcial.slice(1))}</div></div>`
      : `<div class="value ${ahorro > 0 ? 'pos' : ahorro < 0 ? 'neg' : ''}">${M(compact(ahorro))}</div>
      <div class="note">${tasa != null ? pct(tasa, false) + ' de los ingresos' : 'Sin ingresos registrados'}</div></div>`}
    <div class="card kpi c3"><div class="label">Fondo de emergencia</div>
      <div class="value">${meses != null ? nf1.format(meses) + ' meses' : '—'}</div>
      <div class="note">${gtipico ? `de gastos (${M(compact(gtipico))}/mes)` : 'Faltan datos de gastos'}</div>
      ${meta && meses != null ? `<div class="meta"><div class="lim-barra"><div style="width:${Math.min(meses / meta * 100, 100).toFixed(1)}%;background:${meses >= meta ? 'var(--good)' : 'var(--seq)'}"></div></div>
        <div class="note">${meses >= meta ? '✓ Meta cumplida' : 'Meta'}: ${meta} meses</div></div>` : ''}</div>
    <div class="card kpi c3"><div class="label">En cuentas sin invertir</div>
      <div class="value">${M(compact(enCuentas))}</div>
      <div class="note">${nf0.format(pctCuentas)}% del patrimonio</div></div>
    <div class="card kpi c3"><div class="label">Invertido</div>
      <div class="value">${M(compact(R.inversiones_ars))}</div>
      <div class="note">${R.inversiones.length} posiciones · ${total ? nf0.format(R.inversiones_ars / total * 100) : 0}%</div></div>

    ${tarjetasHTML()}
    <div class="card ${tarjetasHTML() ? 'c6' : ''}">
      <h2>Lo más importante</h2>
      ${A ? notaAnalisisAnterior(A) + (A.titular ? `<div class="titular" style="font-size:17px;margin-bottom:12px">${esc(A.titular)}</div>` : '') + alertasHTML(A.alertas, 3) + `<button class="link" data-ir="analisis">Ver análisis completo →</button>`
          + (DATA.mercado?.analisis?.titular ? `<div class="mk-mini"><span class="muted">Mercado:</span> ${esc(DATA.mercado.analisis.titular)} <button class="link" data-ir="mercado">Ver →</button></div>` : '')
          : `<div class="empty">${S.analisis?.error ? 'No se pudo hacer el análisis: ' + esc(S.analisis.error) : 'Sin análisis de Claude en esta corrida.'}</div>`}
    </div>

    ${plataQuieta()}
    <div class="card ${plataQuieta() ? 'c6' : ''}"><h2>Evolución del patrimonio</h2>${lineaPatrimonio()}</div>

    <div class="card c6"><h2>Dónde está tu plata</h2>${hbars(ents, { color: r => entColor(r.k), total })}</div>
    <div class="card c6"><h2>Pesos y dólares</h2>
      ${pmTot ? `<div class="stack">
        <div style="flex:${pm.ARS};background:var(--s1)" data-tip="${esc(`<b>Pesos</b><br>${compact(pm.ARS)}`)}"></div>
        <div style="flex:${pm.USD};background:var(--s3)" data-tip="${esc(`<b>Dólares</b><br>${compact(pm.USD)}`)}"></div></div>
      <div class="legend"><span><i class="dot" style="background:var(--s1)"></i>Pesos <b>${nf0.format(pm.ARS / pmTot * 100)}%</b> ${M(compact(pm.ARS))}</span>
        <span><i class="dot" style="background:var(--s3)"></i>Dólares <b>${nf0.format(pm.USD / pmTot * 100)}%</b> ${M(compact(pm.USD))}</span></div>` : '<div class="empty">Sin datos</div>'}
      ${tc ? `<p class="nota">Dólares valuados a MEP ${M(money(tc))}${S.cotizaciones.blue ? ` · blue ${money(S.cotizaciones.blue.venta)}` : ''}${S.cotizaciones.oficial ? ` · oficial ${money(S.cotizaciones.oficial.venta)}` : ''}</p>` : ''}
    </div>
  </div>`;
}

// ---------- pestaña: Gastos ----------
function dailyChart(mes) {
  const [y, m] = mes.split('-').map(Number);
  const days = new Date(y, m, 0).getDate();
  const byDay = Array(days).fill(0), covered = Array(days).fill(!(R.cobertura || []).length);
  const tc = R.tipo_cambio_mep || 0;
  coberturaMes(mes).forEach(c => { if (c.d) for (let i = +c.d.slice(8) - 1; i <= +c.h.slice(8) - 1; i++) covered[i] = true; });
  S.movimientos.forEach(x => {
    if (x.monto < 0 && x.fecha.startsWith(mes) && !EXCL.has(x.categoria)) byDay[+x.fecha.slice(8, 10) - 1] += -x.monto * (x.moneda === 'USD' ? tc : 1);
  });
  const angosto = innerWidth < 600;
  const W = angosto ? 360 : 720, H = angosto ? 170 : 190, pl = angosto ? 38 : 44, pr = 4, pt = 8, pb = 22;
  const max = Math.max(...byDay, 1);
  const nice = (() => { const p = Math.pow(10, Math.floor(Math.log10(max))); return Math.ceil(max / p) * p; })();
  const bw = (W - pl - pr) / days, yv = v => pt + (H - pt - pb) * (1 - v / nice);
  let g = '';
  covered.forEach((c, i) => { if (!c) g += `<rect x="${pl + i * bw}" y="${pt}" width="${bw}" height="${H - pt - pb}" fill="var(--surface-2)"/>`; });
  for (let i = 0; i <= 4; i++) {
    const v = nice * i / 4, yy = yv(v);
    g += `<line x1="${pl}" x2="${W - pr}" y1="${yy}" y2="${yy}" stroke="var(--grid)"/>`;
    g += `<text class="m" x="${pl - 6}" y="${yy + 4}" text-anchor="end">${compact(v).replace('$ ', '')}</text>`;
  }
  byDay.forEach((v, i) => {
    const x = pl + i * bw, w = Math.max(bw - 2, 1), yy = yv(v), h = H - pb - yy;
    const r = Math.min(4, w / 2, h);
    if (v > 0) g += `<path d="M${x + 1},${H - pb} V${yy + r} q0,-${r} ${r},-${r} h${Math.max(w - 2 * r, 0)} q${r},0 ${r},${r} V${H - pb} Z" fill="var(--seq)"/>`;
    g += `<rect x="${x}" y="${pt}" width="${bw}" height="${H - pt - pb}" fill="transparent" data-tip="${esc(`<b>${i + 1}/${m}</b><br>${covered[i] ? money(v) : 'Sin datos de los reportes'}`)}"/>`;
    if ((i + 1) % (angosto ? 10 : 5) === 0 || i === 0) g += `<text x="${x + bw / 2}" y="${H - 5}" text-anchor="middle">${i + 1}</text>`;
  });
  g += `<line x1="${pl}" x2="${W - pr}" y1="${H - pb}" y2="${H - pb}" stroke="var(--border)"/>`;
  return `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="Gastos por día">${g}</svg>`;
}

function renderGastos(mes) {
  const panel = document.getElementById('p-gastos');
  if (!mes) { panel.innerHTML = '<div class="card"><div class="empty">No hay movimientos. Cargá resúmenes PDF en la carpeta reportes/.</div></div>'; return; }
  const G = R.gastos_por_mes[mes];
  const cob = coberturaMes(mes);
  const ahorro = G.ingresos_ars - G.total_ars;
  const incompleto = calidadMes(mes).sin.length > 0;
  const cats = Object.entries(G.por_categoria).map(([k, v]) => ({ k, v }));
  const ings = Object.entries(G.ingresos_por_categoria).map(([k, v]) => ({ k, v }));
  panel.innerHTML = `<div class="grid">
    <div class="card">
      <div class="filtros">${MESES.slice().reverse().map(x => `<button class="pill" aria-pressed="${x === mes}" data-mes="${x}">${esc(nombreMes(x))}</button>`).join('')}</div>
      <div class="cob">${cob.map(c => `<span><span class="dot" style="background:${entColor(c.entidad)}"></span>${esc(c.entidad)} · ${esc(c.cuenta)}:
        ${c.d ? `${dm(c.d)}–${dm(c.h)}${c.completo ? '' : ' <span class="muted">(parcial)</span>'}` : '<span class="muted">sin reporte</span>'}</span>`).join('') || '<span class="muted">Sin reportes PDF</span>'}</div>
    </div>
    <div class="card trio">
      <div class="kpi"><div class="label">Gastos</div><div class="value">${M(compact(G.total_ars))}</div><div class="note">${G.cantidad} movimientos</div></div>
      <div class="kpi"><div class="label">Ingresos</div><div class="value">${M(compact(G.ingresos_ars))}</div><div class="note">${esc(Object.keys(G.ingresos_por_categoria).slice(0, 2).join(', ') || '—')}</div></div>
      <div class="kpi"><div class="label">Resultado</div>${incompleto ? `<div class="value muted">—</div><div class="note">Mes incompleto</div>`
        : `<div class="value ${ahorro > 0 ? 'pos' : ahorro < 0 ? 'neg' : ''}">${M(compact(ahorro))}</div><div class="note">${G.ingresos_ars ? pct(ahorro / G.ingresos_ars * 100, false) + ' de los ingresos' : '—'}</div>`}</div>
    </div>

    ${limitesHTML(mes)}
    <div class="card c7"><h2>Gastos por día</h2>${dailyChart(mes)}
      <div class="legend" style="margin-top:8px">${Object.entries(G.por_entidad).map(([k, v]) => `<span><i class="dot" style="background:${entColor(k)}"></i>${esc(k)} ${M(`<b>${compact(v)}</b>`)}</span>`).join('')}
        <span class="muted">Gris: días sin reporte</span></div></div>
    <div class="card c5"><h2>En qué gastaste</h2>${hbars(cats, { color: 'var(--seq)', total: G.total_ars })}
      <h2 style="margin-top:20px">De dónde entró</h2>${hbars(ings, { color: 'var(--s3)', total: G.ingresos_ars })}</div>

    <div class="card"><h2>Gastos más grandes</h2><div class="lista">
      ${G.top.map(m => `<div class="fila">
        <div class="t">${esc(m.descripcion)}</div><div class="v">${M(money(m.monto, m.moneda))}</div>
        <div class="d">${dm(m.fecha)} · ${esc(m.entidad)}</div><div class="v2"><span class="tag">${esc(m.categoria)}</span></div></div>`).join('') || '<div class="empty">Sin gastos</div>'}
    </div>
    <p class="nota">No se cuentan las transferencias entre tus cuentas. "Pago de tarjeta" es el pago del resumen; el detalle está en el resumen de la tarjeta.</p></div>
    <div class="card c7"><h2>Ingresos y gastos por mes</h2>${flujoMeses()}</div>
    <div class="card c5"><h2>Gastos fijos y suscripciones</h2>${gastosFijos()}</div>
  </div>`;
  panel.querySelectorAll('[data-mes]').forEach(b => b.onclick = () => { store.set('mes', b.dataset.mes); renderGastos(b.dataset.mes); });
}

// ---------- pestaña: Inversiones ----------
function renderInversiones() {
  const tipos = Object.entries(R.inversiones_por_tipo).map(([k, v]) => ({ k: tipoBonito(k), v }));
  const al = iso => { const d = dias(iso); return iso ? `<span class="${d > 20 ? 'stale' : ''}">al ${dm(iso)}${d > 20 ? ' ⏱' : ''}</span>` : ''; };
  document.getElementById('p-inversiones').innerHTML = `<div class="grid">
    <div class="card kpi c4"><div class="label">Invertido</div><div class="value">${M(compact(R.inversiones_ars))}</div>
      <div class="note">${R.inversiones.length} posiciones</div></div>
    <div class="card kpi c4"><div class="label">En cuentas</div><div class="value">${M(compact(R.liquidez_ars))}</div>
      <div class="note">Pesos: ${M(compact(R.pesos_liquidos_ars))}</div></div>
    <div class="card kpi c4"><div class="label">Mayor posición</div>
      <div class="value" style="font-size:18px">${R.inversiones[0] ? esc(R.inversiones[0].activo) : '—'}</div>
      <div class="note">${R.inversiones[0]?.peso_pct != null ? nf1.format(R.inversiones[0].peso_pct) + '% de la cartera' : ''}</div></div>

    <div class="card c7"><h2>Posiciones</h2><div class="lista">
      ${R.inversiones.map(i => `<div class="fila">
        <div class="t"><span class="dot" style="background:${entColor(i.entidad)}"></span>${esc(i.activo)}</div>
        <div class="v">${M(money(i.valuacion, i.moneda))}</div>
        <div class="d">${esc(tipoBonito(i.tipo))} · ${esc(i.entidad)} · ${al(i.al)}</div>
        <div class="v2">${i.peso_pct != null ? nf1.format(i.peso_pct) + '%' : ''}${i.ganancia_pct != null ? ` · <span class="${i.ganancia_pct >= 0 ? 'pos' : 'neg'}">${pct(i.ganancia_pct)}</span>` : ''}</div>
      </div>`).join('') || '<div class="empty">Sin inversiones</div>'}
    </div></div>
    <div class="card c5"><h2>Por tipo</h2>${hbars(tipos, { color: 'var(--seq)', total: R.inversiones_ars })}</div>

    <div class="card"><h2>Cuentas</h2><div class="lista">
      ${R.liquidez.map(c => `<div class="fila">
        <div class="t"><span class="dot" style="background:${entColor(c.entidad)}"></span>${esc(c.tipo)}</div>
        <div class="v">${M(money(c.saldo, c.moneda, true))}</div>
        <div class="d">${esc(c.entidad)} · ${al(c.al)}</div>
        <div class="v2">${c.moneda === 'USD' && c.ars ? M('≈ ' + compact(c.ars)) : ''}</div>
      </div>`).join('') || '<div class="empty">Sin cuentas</div>'}
    </div></div>
  </div>`;
}

// Aviso cuando se muestra un análisis de una actualización anterior
function notaAnalisisAnterior(A) {
  if (!A || !A.anterior) return '';
  const f = A.fecha ? new Date(A.fecha).toLocaleString('es-AR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : 'una actualización anterior';
  return `<p class="nota" style="margin:0 0 10px">⏱ Análisis del ${esc(f)}: en esta actualización no se volvió a analizar${A.error_nuevo ? ' (' + esc(A.error_nuevo) + ')' : ''}. Los números de las otras pestañas sí están al día.</p>`;
}

// ---------- piezas visuales compartidas por Análisis y Mercado ----------
const primeraFrase = t => { const m = String(t || '').match(/^.*?[.!?](\s|$)/); return (m ? m[0] : String(t || '')).trim(); };
const restoFrases = t => String(t || '').slice(primeraFrase(t).length).trim();
const mas = (txt, html) => html ? `<details class="mas"><summary>${txt}</summary><div>${html}</div></details>` : '';
const ESTADO = { bien: ['var(--good)', '✓', 'bien'], regular: ['var(--warning)', '!', 'regular'], mal: ['var(--critical)', '✕', 'mal'] };
function anillo(valor, max, color, centro, sub) {
  const r = 26, c = 2 * Math.PI * r, f = Math.max(0, Math.min(1, valor / max));
  return `<div class="anillo"><svg viewBox="0 0 64 64" aria-hidden="true"><circle cx="32" cy="32" r="${r}" fill="none" stroke="var(--surface-2)" stroke-width="7"/>
    <circle cx="32" cy="32" r="${r}" fill="none" stroke="${color}" stroke-width="7" stroke-linecap="round" stroke-dasharray="${(c * f).toFixed(1)} ${c.toFixed(1)}" transform="rotate(-90 32 32)"/></svg>
    <div class="centro"><b>${centro}</b>${sub ? `<span>${sub}</span>` : ''}</div></div>`;
}
// Escala de 1 a 5 con marcas opcionales (ej. tu cartera y tu perfil)
function escala5(v, marcas = []) {
  return `<div class="escala">${[1, 2, 3, 4, 5].map(i => `<i class="${i <= v ? 'on' : ''}"></i>`).join('')}
    ${marcas.map(m => `<span class="marca" style="left:${((m.v - 0.5) / 5 * 100).toFixed(1)}%" title="${esc(m.t)}">${esc(m.t)}</span>`).join('')}</div>`;
}
const salColor = n => n >= 75 ? 'var(--good)' : n >= 50 ? 'var(--warning)' : 'var(--critical)';

// ---------- pestaña: Análisis ----------
function renderAnalisis() {
  const A = S.analisis;
  const p = document.getElementById('p-analisis');
  if (!A || A.error) {
    p.innerHTML = `<div class="card"><div class="empty">${A?.error ? 'No se pudo hacer el análisis: ' + esc(A.error) : 'Todavía no hay análisis con IA. Tildá "Análisis con IA" al actualizar.'}</div></div>`;
    return;
  }
  const titular = A.titular || primeraFrase(A.resumen);
  const bajada = A.titular ? A.resumen : restoFrases(A.resumen);
  const sal = A.salud && A.salud.puntaje != null ? A.salud : null;
  const o = { alto: 0, medio: 1, bajo: 2 };
  const recos = (A.recomendaciones || []).slice().sort((a, b) => (o[a.impacto] ?? 3) - (o[b.impacto] ?? 3));
  const alertas = (A.alertas || []).slice().sort((a, b) => (NIVEL[a.nivel] || NIVEL.baja)[2] - (NIVEL[b.nivel] || NIVEL.baja)[2]);
  p.innerHTML = `${notaAnalisisAnterior(A)}<div class="grid">
    <div class="card titular-card">
      ${sal ? anillo(sal.puntaje, 100, salColor(sal.puntaje), nf0.format(sal.puntaje), esc(sal.etiqueta || '')) : ''}
      <div><div class="titular">${esc(titular)}</div>${bajada ? `<p class="bajada">${esc(bajada)}</p>` : ''}</div>
    </div>
    ${A.indicadores?.length ? `<div class="card"><div class="tiles">${A.indicadores.map(i => {
      const [c, ic, txt] = ESTADO[i.estado] || ESTADO.regular;
      return `<div class="tile"><div class="tile-cab"><span class="estado" style="background:${c};color:${tinta(c)}" aria-label="${txt}">${ic}</span>${esc(i.nombre)}</div><div class="tile-v">${M(esc(i.valor || '—'))}</div></div>`;
    }).join('')}</div></div>` : ''}
    <div class="card c6"><h2>Qué hacer</h2>${recos.length ? recos.map(r => `<div class="accion-f">
        <span class="flecha">→</span>
        <div><div class="t">${esc(r.titulo)}</div>
          <div class="meta"><span class="tag imp-${esc(r.impacto || 'bajo')}">impacto ${esc(r.impacto || '—')}</span>${r.ahorro_mensual_ars ? `<span class="pos">${M('+' + compact(+r.ahorro_mensual_ars))} por mes</span>` : ''}</div>
          ${mas('Cómo', esc(r.detalle))}</div></div>`).join('') : '<div class="empty">Sin recomendaciones.</div>'}</div>
    <div class="card c6"><h2>Alertas</h2>${alertas.length ? alertas.map(a => {
      const [c, i] = NIVEL[a.nivel] || NIVEL.baja;
      return `<div class="accion-f"><span class="ico-n" style="background:${c};color:${tinta(c)}">${i}</span>
        <div><div class="t">${esc(a.titulo)}</div><div class="meta"><span class="muted">${esc(a.nivel)}</span></div>${mas('Detalle', esc(a.detalle))}</div></div>`;
    }).join('') : '<div class="empty">Sin alertas.</div>'}</div>
    ${A.observaciones?.length ? `<div class="card"><h2>Para tener en cuenta</h2><div class="chips">${A.observaciones.map(x => `<span>${esc(x)}</span>`).join('')}</div>
      <p class="nota">Análisis automático e informativo; no es asesoramiento financiero profesional.</p></div>` : ''}
  </div>`;
}

// ---------- pestaña: Mercado (solo lectura: Pluto analiza y recomienda, nunca opera) ----------
const MK = DATA.mercado;
const ACCION = { comprar: ['var(--good)', '▲'], aumentar: ['var(--good)', '▲'], vender: ['var(--critical)', '▼'],
  reducir: ['var(--serious)', '▼'], cambiar: ['var(--s1)', '⇄'], mantener: ['var(--text-3)', '='] };
const accionDe = a => ACCION[(a || '').toLowerCase()] || ACCION.mantener;
const chipAccion = a => { const [bg, ic] = accionDe(a); return `<span class="chip" style="background:${bg};color:${tinta(bg)}">${ic} ${esc(a || '—')}</span>`; };
const nivelPts = n => { const k = { baja: 1, media: 2, alta: 3 }[n] || 0; return `<span class="pts" aria-label="${esc(n || '?')}">${[1, 2, 3].map(i => `<i class="${i <= k ? 'on' : ''}"></i>`).join('')}</span>`; };
const IMPACTO = { positivo: ['var(--good)', '▲', 'pos'], negativo: ['var(--critical)', '▼', 'neg'], neutral: ['var(--text-3)', '●', 'muted'],
  incierto: ['var(--warning)', '?', 'muted'], mixto: ['var(--warning)', '◆', 'muted'] };
const SENT = { positivo: ['var(--good)', '▲ Positivo'], neutral: ['var(--text-3)', '● Neutral'], negativo: ['var(--critical)', '▼ Negativo'] };
const SERIES = ['var(--s1)', 'var(--s2)', 'var(--s3)', 'var(--s4)', 'var(--s5)', 'var(--text-3)'];

function sparkline(serie, w = 120, h = 34) {
  if (!serie || serie.length < 2) return '';
  const v = serie.map(x => +x[1]), lo = Math.min(...v), hi = Math.max(...v), r = hi - lo || 1;
  const pts = v.map((y, i) => `${(i / (v.length - 1) * w).toFixed(1)},${(h - 2 - (y - lo) / r * (h - 4)).toFixed(1)}`).join(' ');
  const c = v[v.length - 1] >= v[0] ? 'var(--good-text)' : 'var(--neg-text)';
  return `<svg class="spark" viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><polyline points="${pts}" fill="none" stroke="${c}" stroke-width="2" stroke-linejoin="round" vector-effect="non-scaling-stroke"/></svg>`;
}

function termometroHTML(T) {
  if (!T) return '';
  const sent = SENT[T.sentimiento];
  return `<div class="termo">
    ${T.riesgo_cartera ? `<div><div class="termo-l">Riesgo <span class="muted">· tu cartera ${T.riesgo_cartera}/5, tu perfil ${T.riesgo_perfil || '?'}/5</span></div>
      ${escala5(T.riesgo_cartera, T.riesgo_perfil ? [{ v: T.riesgo_perfil, t: 'perfil' }] : [])}</div>` : ''}
    ${T.diversificacion ? `<div><div class="termo-l">Diversificación <span class="muted">· ${T.diversificacion}/5</span></div>${escala5(T.diversificacion)}</div>` : ''}
    ${sent ? `<div><div class="termo-l">Noticias</div><span class="sent" style="color:${sent[0]}">${sent[1]}</span></div>` : ''}
  </div>`;
}

function distribucionHTML(filas) {
  if (!filas?.length) return '<div class="empty">Sin propuesta de distribución.</div>';
  const barra = k => `<div class="stack100">${filas.map((f, i) => { const v = +f[k] || 0; return v ? `<div style="flex:${v};background:${SERIES[i % SERIES.length]}" data-tip="${esc(`<b>${esc(f.clase)}</b><br>${nf1.format(v)}%`)}"></div>` : ''; }).join('')}</div>`;
  return `<div class="dist"><span class="dist-l">Hoy</span>${barra('actual_pct')}<span class="dist-l">Objetivo</span>${barra('objetivo_pct')}</div>
    <div class="dist-ley">${filas.map((f, i) => { const a = +f.actual_pct || 0, o = +f.objetivo_pct || 0, d = o - a;
      return `<div data-tip="${esc(f.comentario || '')}"><span class="dot" style="background:${SERIES[i % SERIES.length]}"></span><span class="n">${esc(f.clase)}</span>
        <span class="v">${nf0.format(a)}% → <b>${nf0.format(o)}%</b></span><span class="dd ${d > 0 ? 'pos' : d < 0 ? 'neg' : 'muted'}">${d > 0 ? '▲' : d < 0 ? '▼' : '='}${d ? ' ' + nf0.format(Math.abs(d)) : ''}</span></div>`; }).join('')}</div>`;
}

function recoTile(r) {
  const [c, ic] = accionDe(r.accion);
  const detalle = [r.motivo && `<p><b>Por qué:</b> ${esc(r.motivo)}</p>`, r.riesgos && `<p><b>Riesgos:</b> ${esc(r.riesgos)}</p>`,
    r.horizonte && `<p><b>Plazo:</b> ${esc(r.horizonte)}</p>`].filter(Boolean).join('');
  return `<div class="reco-t" style="--c:${c};--fc:${tinta(c)}">
    <div class="reco-cab"><span class="reco-ic">${ic}</span><span class="reco-acc">${esc(r.accion || '')}</span>${nivelPts(r.confianza)}</div>
    <div class="reco-act">${esc(r.activo)}${r.por ? `<span class="muted"> → </span>${esc(r.por)}` : ''}</div>
    ${r.titulo ? `<div class="reco-tit">${esc(r.titulo)}</div>` : ''}
    ${r.monto_ars ? `<div class="reco-monto">${M('≈ ' + compact(+r.monto_ars))}</div>` : ''}
    ${mas('Por qué', detalle)}</div>`;
}

function noticiasHTML(A) {
  const ns = A.noticias || [];
  if (!ns.length) return `<div class="empty">${A.con_noticias === false ? 'Este proveedor de IA no busca en la web. Con Claude Code o la API de Anthropic se suman noticias.' : 'Sin noticias relevantes para tus activos.'}</div>`;
  return ns.map(n => { const [c, ic] = IMPACTO[n.impacto] || IMPACTO.neutral;
    return `<div class="accion-f"><span class="ico-n" style="background:${c};color:${tinta(c)}" aria-label="${esc(n.impacto || '')}">${ic}</span>
      <div><div class="t">${esc(n.titulo)}</div>
      <div class="meta">${(n.activos || []).map(a => `<span class="tag">${esc(a)}</span>`).join('')}<span class="muted">${esc(n.fuente || '')}${n.fecha ? ' · ' + esc(dm(n.fecha)) : ''}</span></div>
      ${mas('Qué significa', esc(n.que_significa))}</div></div>`; }).join('');
}

function escenariosHTML(es) {
  if (!es?.length) return '<div class="empty">—</div>';
  return '<div class="escen">' + es.map(e => {
    const tipo = IMPACTO[e.efecto] ? e.efecto : 'mixto';
    const [c, ic] = IMPACTO[tipo];
    const detalle = e.detalle || (IMPACTO[e.efecto] ? '' : e.efecto);
    return `<div class="esc" style="--c:${c};--fc:${tinta(c)}"><div class="esc-cab"><span class="reco-ic">${ic}</span><span class="muted">Probabilidad</span>${nivelPts(e.probabilidad)}</div>
      <div class="t">${esc(e.escenario)}</div>${detalle ? `<div class="d">${esc(detalle)}</div>` : ''}${mas('Qué considerar', esc(e.que_considerar))}</div>`;
  }).join('') + '</div>';
}

function preciosHTML(precios) {
  const tengo = new Set(R.inversiones.map(i => i.activo));
  const ent = Object.entries(precios || {}).sort((a, b) => tengo.has(b[0]) - tengo.has(a[0]) || a[0].localeCompare(b[0]));
  if (!ent.length) return '<div class="empty">Sin precios: activá IOL en Configuración → Fuentes y sumá activos a seguir en Análisis de mercado.</div>';
  return '<div class="precios">' + ent.map(([sim, p]) => {
    const i = p.indicadores || {};
    const precio = p.precio ?? i.ultimo;
    return `<div class="precio" data-tip="${esc(`<b>${esc(sim)}</b><br>Volatilidad anual ${i.volatilidad_anual != null ? nf1.format(i.volatilidad_anual) + '%' : '—'}<br>Caída máxima (12m) ${pct(i.caida_maxima)}<br>Contra su máximo ${pct(i.vs_maximo)}`)}">
      <div class="cab"><b>${esc(sim)}</b><span class="tag">${tengo.has(sim) ? 'tenés' : 'seguís'}</span></div>
      <div class="v">${precio != null ? money(precio, p.moneda === 'USD' ? 'USD' : 'ARS', true) : '—'}
        ${p.variacion_dia != null ? `<span class="${p.variacion_dia >= 0 ? 'pos' : 'neg'}">${pct(p.variacion_dia)}</span>` : ''}</div>
      ${sparkline(p.serie)}
      <div class="rends">${[['1m', i.rend_1m], ['3m', i.rend_3m], ['12m', i.rend_12m]].map(([k, v]) => `<span>${k} <b class="${v == null ? '' : v >= 0 ? 'pos' : 'neg'}">${pct(v)}</b></span>`).join('')}</div>
    </div>`;
  }).join('') + '</div>';
}

function seguimientoHTML(seg, ac) {
  if (!seg?.length) return '<div class="empty">Cada análisis guarda sus recomendaciones con el precio del día. En 7 días vas a ver acá si acertaron.</div>';
  const fila = r => {
    const res = r.acierto == null ? '<span class="muted">⏱ pendiente</span>' : r.acierto ? '<span class="pos">✓ acertó</span>' : '<span class="neg">✕ no acertó</span>';
    return `<div class="fila seg"><div class="t">${chipAccion(r.accion)}${esc(r.activo)}${r.por ? ' → ' + esc(r.por) : ''}</div><div class="v">${res}</div>
      <div class="d">${esc(dm(r.fecha))} · hace ${r.dias} días</div>
      <div class="v2">${r.variacion_pct != null ? `<span class="${r.variacion_pct >= 0 ? 'pos' : 'neg'}">${pct(r.variacion_pct)}</span>` : 'sin precio'}</div></div>`;
  };
  const tasa = ac.medibles ? ac.aciertos / ac.medibles * 100 : null;
  return `<div class="aciertos">
      ${tasa != null ? anillo(tasa, 100, salColor(tasa), nf0.format(tasa) + '%', 'aciertos') : anillo(0, 100, 'var(--text-3)', '—', 'sin medir')}
      <div><div class="titular" style="font-size:20px">${ac.medibles ? `${ac.aciertos} de ${ac.medibles} acertaron` : 'Todavía sin medir'}</div>
      <p class="bajada">${ac.medibles ? 'Recomendaciones de 7 días o más que fueron en la dirección correcta.' : 'Las recomendaciones se miden a partir de los 7 días.'}</p></div></div>
    <div class="lista">${seg.slice(0, 4).map(fila).join('')}</div>
    ${seg.length > 4 ? mas(`Ver las ${seg.length} recomendaciones`, `<div class="lista">${seg.slice(4).map(fila).join('')}</div>`) : ''}
    <p class="nota">Comprar o aumentar acierta si el precio subió; vender o reducir, si bajó; cambiar, si el destino rindió más. No incluye dividendos, cupones ni costos.</p>`;
}

function renderMercado() {
  const p = document.getElementById('p-mercado');
  if (!MK) return;
  const A = MK.analisis;
  const aviso = `<div class="solo-lectura">🛈 <b>Pluto solo recomienda, no opera.</b> Vos decidís y operás en tu broker. No es asesoramiento financiero.</div>`;
  let cuerpo;
  if (!A || A.error) {
    cuerpo = `<div class="card"><div class="empty">${A?.error ? 'No se pudo hacer el análisis de mercado: ' + esc(A.error) : 'Todavía no hay análisis de mercado. Tildá "Análisis de mercado" al actualizar.'}</div></div>`;
  } else {
    const f = A.fecha ? new Date(A.fecha).toLocaleString('es-AR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' }) : '';
    const titular = A.titular || primeraFrase(A.resumen);
    const puntos = A.puntos_clave?.length ? A.puntos_clave : [];
    cuerpo = `<div class="card mk-hero">
        <div><div class="titular">${esc(titular)}</div>
          ${puntos.length ? `<ul class="puntos">${puntos.map(x => `<li>${esc(x)}</li>`).join('')}</ul>` : ''}
          ${mas('Leer el análisis completo', esc(A.titular ? A.resumen : restoFrases(A.resumen)))}
          <p class="nota">${esc(f)}${A.proveedor ? ' · ' + esc(A.proveedor) : ''} · ${A.con_noticias ? 'con noticias de la web' : 'sin noticias'}</p></div>
        ${termometroHTML(A.termometro)}
      </div>
      <div class="card"><h2>Qué hacer</h2>${A.recomendaciones?.length ? `<div class="recos">${A.recomendaciones.map(recoTile).join('')}</div>` : '<div class="empty">La IA no sugiere cambios por ahora.</div>'}</div>
      <div class="card c6"><h2>Distribución sugerida</h2>${distribucionHTML(A.cartera_objetivo)}</div>
      <div class="card c6"><h2>Noticias</h2>${noticiasHTML(A)}</div>
      <div class="card"><h2>Escenarios</h2>${escenariosHTML(A.escenarios)}</div>`;
  }
  p.innerHTML = aviso + notaAnalisisAnterior(A) + `<div class="grid">${cuerpo}
    <div class="card"><h2>Precios</h2>${preciosHTML(MK.precios)}</div>
    <div class="card"><h2>¿Acertaron?</h2>${seguimientoHTML(MK.seguimiento, MK.aciertos || {})}</div>
  </div>`;
}

// ---------- navegación ----------
function irA(tab) {
  document.querySelectorAll('nav.tabs button').forEach(b => b.setAttribute('aria-selected', b.dataset.tab === tab));
  document.querySelectorAll('.panel').forEach(p => p.hidden = p.id !== 'p-' + tab);
  store.set('tab', tab);
  window.scrollTo(0, 0);
}

function init() {
  const f = new Date(S.fecha);
  document.getElementById('sub').textContent = 'Actualizado ' + f.toLocaleString('es-AR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' });
  if (DATA.demo) document.getElementById('demo').innerHTML = '<span class="demo">DEMO</span>';
  renderResumen();
  const mesGuardado = store.get('mes');
  renderGastos(MESES.includes(mesGuardado) ? mesGuardado : (MESES[MESES.length - 1] || null));
  renderInversiones();
  renderAnalisis();
  if (MK) renderMercado(); else document.querySelector('[data-tab="mercado"]').hidden = true;

  document.querySelectorAll('nav.tabs button').forEach(b => b.onclick = () => irA(b.dataset.tab));
  // La app de escritorio puede pedir abrir una pestaña (solo navegación, nada más)
  window.addEventListener('message', e => {
    const t = e.data && e.data.ir;
    const b = typeof t === 'string' && document.querySelector(`nav.tabs button[data-tab="${CSS.escape(t)}"]`);
    if (b && !b.hidden) irA(t);
  });
  document.addEventListener('click', e => { const t = e.target.closest('[data-ir]'); if (t) irA(t.dataset.ir); });
  const tabGuardada = store.get('tab');
  irA(['resumen', 'gastos', 'inversiones', 'analisis'].concat(MK ? ['mercado'] : []).includes(tabGuardada) ? tabGuardada : 'resumen');

  const bp = document.getElementById('btn-privado');
  const setPriv = on => { document.body.classList.toggle('privado', on); bp.setAttribute('aria-pressed', on); store.set('privado', on ? '1' : '0'); };
  setPriv(store.get('privado') === '1');
  bp.onclick = () => setPriv(!document.body.classList.contains('privado'));

  // Oscuro por defecto; si elegiste claro, se recuerda
  const r = document.documentElement;
  if (store.get('tema') === 'light') r.dataset.theme = 'light';
  document.getElementById('btn-tema').onclick = () => {
    r.dataset.theme = r.dataset.theme === 'light' ? 'dark' : 'light';
    store.set('tema', r.dataset.theme);
  };
}
init();

// ---------- tooltip (mouse y toque) ----------
const tip = document.getElementById('tip');
function mostrarTip(e, t) {
  if (!t) { tip.style.opacity = 0; return; }
  tip.innerHTML = t.dataset.tip;
  const x = Math.max(8, Math.min(e.clientX + 12, innerWidth - tip.offsetWidth - 8));
  const y = e.clientY - tip.offsetHeight - 12 < 0 ? e.clientY + 16 : e.clientY - tip.offsetHeight - 12;
  tip.style.left = x + 'px'; tip.style.top = y + 'px'; tip.style.opacity = 1;
}
document.addEventListener('mousemove', e => mostrarTip(e, e.target.closest('[data-tip]')));
document.addEventListener('touchstart', e => { const p = e.touches[0]; mostrarTip(p, e.target.closest('[data-tip]')); }, { passive: true });
