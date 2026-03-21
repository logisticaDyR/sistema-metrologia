/**
 * Tatronics — UI Helpers
 * Toast, modals, panel navigation, and DOM utilities.
 */
'use strict';

// ── State ──────────────────────────────────────────────────────────────────
let currentPanel = 'dashboard';

// ── Toast ──────────────────────────────────────────────────────────────────
let _toastTimer;
function toast(msg, type = 'ok') {
  const t    = document.getElementById('toast');
  const icon = document.getElementById('toast-icon');
  const txt  = document.getElementById('toast-msg');
  if (!t || !icon || !txt) return;
  const icons = { ok: '✅', error: '❌', warn: '⚠️', info: 'ℹ️', loading: '⏳' };
  icon.textContent = icons[type] || '✅';
  txt.textContent  = msg;
  t.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), type === 'loading' ? 60000 : 3800);
}
function toastClear() {
  clearTimeout(_toastTimer);
  document.getElementById('toast')?.classList.remove('show');
}

// ── Modals ─────────────────────────────────────────────────────────────────
function openModal(id) {
  document.getElementById(id)?.classList.add('open');
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove('open');
}

// Close on backdrop click
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.modal-overlay').forEach(m => {
    m.addEventListener('click', e => {
      if (e.target === m) m.classList.remove('open');
    });
  });
});

// ── Panel navigation ────────────────────────────────────────────────────────
const PANEL_TITLES = {
  'dashboard':          ['Dashboard', 'Inicio'],
  'nuevo-diagnostico':  ['Nuevo Diagnóstico', 'Diagnóstico'],
  'historial':          ['Historial de Diagnósticos', 'Historial'],
  'equipos':            ['Inventario de Equipos', 'Equipos'],
  'patrones':           ['Patrones de Referencia', 'Patrones'],
  'clientes':           ['Gestión de Clientes', 'Clientes'],
  'personal':           ['Personal del Laboratorio', 'Personal'],
  'certificados':       ['Certificados PDF', 'Certificados'],
  'estadisticas':       ['Estadísticas', 'Estadísticas'],
  'alertas':            ['Centro de Alertas', 'Alertas'],
  'auditoria':          ['Registro de Auditoría', 'Auditoría'],
};

const PANEL_LOADERS = {};  // filled by app.js

function showPanel(id) {
  // Hide all panels
  document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));
  // Deactivate all nav items
  document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));

  const el = document.getElementById('panel-' + id);
  if (el) el.classList.add('active');

  const ni = document.querySelector(`.nav-item[data-panel="${id}"]`);
  if (ni) ni.classList.add('active');

  const titles = PANEL_TITLES[id];
  if (titles) {
    const ttl = document.getElementById('topbar-title');
    const bc  = document.getElementById('topbar-bc-sub');
    if (ttl) ttl.textContent = titles[0];
    if (bc)  bc.textContent  = titles[1];
  }

  currentPanel = id;

  if (PANEL_LOADERS[id]) PANEL_LOADERS[id]();
}

function registerPanelLoader(panelId, fn) {
  PANEL_LOADERS[panelId] = fn;
}

// ── Value helper ────────────────────────────────────────────────────────────
function v(id) {
  return (document.getElementById(id)?.value || '').trim();
}

// ── Add-days helper ─────────────────────────────────────────────────────────
function addDays(dateStr, days) {
  const d = new Date(dateStr);
  d.setDate(d.getDate() + days);
  return d.toISOString().substring(0, 10);
}

// ── Result badge helpers ────────────────────────────────────────────────────
const RESULT_COLORS = {
  conforme:    'badge-green',
  no_conforme: 'badge-red',
  observacion: 'badge-yellow',
  pendiente:   'badge-blue',
};
const RESULT_LABELS = {
  conforme:    'Conforme',
  no_conforme: 'No conforme',
  observacion: 'Con observ.',
  pendiente:   'Pendiente',
};

function resultBadge(resultado) {
  const cls = RESULT_COLORS[resultado] || 'badge-blue';
  const lbl = RESULT_LABELS[resultado] || resultado;
  return `<span class="badge ${cls}"><span class="badge-dot"></span>${lbl}</span>`;
}
