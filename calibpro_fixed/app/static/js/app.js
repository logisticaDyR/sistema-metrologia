/**
 * Tatronics — App
 * Panel loaders, modals CRUD, global search, and app initialization.
 * Depends on: api.js, ui.js, wizard.js
 */
'use strict';

// ══════════════════════════════════════════
//  DASHBOARD
// ══════════════════════════════════════════
async function loadDashboard() {
  const d = await Dashboard.stats();
  if (!d) return;

  setText('s-diag',  d.diag_mes);
  setText('s-conf',  d.conformes);
  setText('s-nc',    d.no_conformes);
  setText('s-alert', d.alertas);

  // Alert badge
  const dot    = document.getElementById('alert-dot');
  const badge  = document.getElementById('nb-alerts');
  if (dot)   dot.style.display   = d.alertas > 0 ? 'block' : 'none';
  if (badge) badge.textContent   = d.alertas;

  // Vencimientos table
  const vencTbody = document.querySelector('#tbl-venc tbody');
  if (vencTbody) {
    const today = new Date().toISOString().substring(0, 10);
    vencTbody.innerHTML = (d.vencimientos || []).map(v => {
      const color = v.prox && v.prox < addDays(today, 15) ? 'var(--danger)' :
                    v.prox && v.prox < addDays(today, 30) ? 'var(--warn)'   : 'var(--text)';
      return `<tr>
        <td><b>${v.equipo_codigo || ''}</b><br><span style="font-size:11px;color:var(--text3)">${v.descripcion || ''}</span></td>
        <td>${v.magnitud || ''}</td>
        <td style="font-family:'DM Mono',monospace;font-size:12px;color:${color}">${v.prox || 'Sin dato'}</td>
      </tr>`;
    }).join('') || '<tr><td colspan="3" style="text-align:center;color:var(--text3);padding:20px">Sin equipos registrados</td></tr>';
  }

  // Recientes timeline
  const rec = document.getElementById('dash-recientes');
  if (rec) {
    rec.innerHTML = (d.recientes || []).map(r => `
      <div class="tl-item">
        <div class="tl-dot ${r.resultado === 'no_conforme' ? 'red' : r.resultado === 'observacion' ? 'warn' : ''}"></div>
        <div class="tl-date">${(r.fecha_fin || 'En progreso').substring(0, 10)}</div>
        <div class="tl-text">${r.n_certificado || '—'} — ${r.equipo_codigo || ''}</div>
        <div class="tl-sub">${r.equipo_desc || ''} · ${r.resultado || ''}</div>
      </div>`).join('') || '<p style="color:var(--text3);font-size:13px;padding:12px 0">Sin actividad reciente.</p>';
  }

  // Magnitudes chart
  const magGrid = document.getElementById('dash-magnitudes');
  if (magGrid) {
    const maxMag = Math.max(1, ...(d.por_magnitud || []).map(m => m.total));
    const icons  = { Presión: '🔵', Temperatura: '🌡️', Peso: '⚖️', Eléctrica: '⚡', Dimensional: '📏', pH: '🧪', Caudal: '💧', Vibración: '🔊' };
    magGrid.innerHTML = (d.por_magnitud || []).map(m => `
      <div class="mag-item">
        <div class="mag-icon">${icons[m.magnitud] || '📊'}</div>
        <div class="mag-val">${m.total}</div>
        <div class="mag-lbl">${m.magnitud}</div>
        <div class="prog"><div class="prog-fill" style="width:${Math.round(m.total / maxMag * 100)}%"></div></div>
      </div>`).join('') || '<p style="color:var(--text3);font-size:13px;">Sin diagnósticos registrados.</p>';
  }
}

// ══════════════════════════════════════════
//  HISTORIAL
// ══════════════════════════════════════════
let _histPage = 1;

async function deleteDiagnostico(id, cert) {
  if (!confirm(`¿Eliminar el diagnóstico "${cert}"?\nEsta acción no se puede deshacer.`)) return;
  const res = await Diagnosticos.remove(id);
  if (res?.ok) { toast('Diagnóstico eliminado'); loadHistorial(); loadCertificados(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function loadHistorial(page) {
  if (page !== undefined) _histPage = page;
  const q   = v('hist-q');
  const mag = v('hist-mag');
  const d   = await Diagnosticos.list({ q, magnitud: mag, page: _histPage });
  if (!d) return;

  const tbody = document.getElementById('tbl-historial');
  if (tbody) {
    tbody.innerHTML = (d.data || []).map(r => `
      <tr>
        <td style="font-family:'DM Mono',monospace;font-size:11px;color:var(--accent)">${r.n_certificado || '—'}</td>
        <td><b>${r.equipo_codigo || ''}</b><br><span style="font-size:11px;color:var(--text3)">${(r.equipo_desc || '').substring(0, 32)}</span></td>
        <td>${r.magnitud || ''}</td>
        <td>${r.tecnico || ''}</td>
        <td>${r.cliente || ''}</td>
        <td style="font-family:'DM Mono',monospace;font-size:11px">${(r.fecha_fin || '').substring(0, 10) || '—'}</td>
        <td>${resultBadge(r.resultado)}</td>
        <td>
          <div style="display:flex;gap:4px">
            <button class="btn-sec btn-sm" onclick="verPDFById(${r.id})" title="Ver PDF">📄</button>
            <button class="btn-info btn-sm" onclick="openEmailModalById(${r.id})" title="Enviar email">📧</button>
            <button class="btn-danger-sm" onclick="deleteDiagnostico(${r.id},'${(r.n_certificado||'').replace(/'/g,'')}')" title="Eliminar">🗑️</button>
          </div>
        </td>
      </tr>`).join('') ||
      '<tr><td colspan="8" style="text-align:center;color:var(--text3);padding:24px">Sin registros</td></tr>';
  }

  const pagination = document.getElementById('hist-pagination');
  if (pagination) {
    pagination.innerHTML = '';
    if (d.total > 20) {
      const pages = Math.ceil(d.total / 20);
      for (let p = 1; p <= pages; p++) {
        const btn = document.createElement('button');
        btn.className = `btn-sec btn-sm ${p === _histPage ? 'active' : ''}`;
        btn.style.margin = '0 2px';
        btn.textContent = p;
        btn.onclick = () => loadHistorial(p);
        pagination.appendChild(btn);
      }
    } else {
      pagination.textContent = `${d.data.length} de ${d.total} registros`;
    }
  }
}

// ══════════════════════════════════════════
//  EQUIPOS
// ══════════════════════════════════════════
async function deleteEquipo(id, codigo) {
  if (!confirm(`¿Dar de baja el equipo "${codigo}"?\nSus diagnósticos se conservarán en el historial.`)) return;
  const res = await Equipos.remove(id);
  if (res?.ok) { toast('Equipo dado de baja'); loadEquipos(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function loadEquipos() {
  const q    = v('eq-q');
  const data = await Equipos.list(q);
  if (!data) return;

  const today = new Date().toISOString().substring(0, 10);
  const tbody = document.getElementById('tbl-equipos');
  if (!tbody) return;

  tbody.innerHTML = data.map(e => {
    let estado = 'badge-green', etiq = 'Vigente';
    if (e.prox_calibracion && e.prox_calibracion < today)           { estado = 'badge-red';    etiq = 'Vencida';    }
    else if (e.prox_calibracion && e.prox_calibracion < addDays(today, 30)) { estado = 'badge-yellow'; etiq = 'Por vencer'; }
    return `<tr>
      <td style="font-family:'DM Mono',monospace;font-size:12px">${e.codigo}</td>
      <td><b>${e.descripcion}</b><br><span style="font-size:11px;color:var(--text3)">${e.fabricante || ''} ${e.modelo || ''}</span></td>
      <td>${e.magnitud || ''}</td>
      <td>${e.ubicacion || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${(e.ultima_calibracion || '').substring(0, 10) || '—'}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${(e.prox_calibracion || '').substring(0, 10) || '—'}</td>
      <td><span class="badge ${estado}"><span class="badge-dot"></span>${etiq}</span></td>
      <td>
        <div style="display:flex;gap:4px">
          <button class="btn-primary-sm" onclick="calibrarEquipo(${e.id},'${e.codigo}')">Calibrar</button>
          <button class="btn-danger-sm" onclick="deleteEquipo(${e.id},'${e.codigo.replace(/'/g,'')}')" title="Dar de baja">🗑️</button>
        </div>
      </td>
    </tr>`;
  }).join('') || '<tr><td colspan="8" style="text-align:center;color:var(--text3);padding:24px">Sin equipos registrados</td></tr>';
}

function calibrarEquipo(id, codigo) {
  showPanel('nuevo-diagnostico');
  setTimeout(() => {
    const sel = document.getElementById('f-equipo-id');
    if (sel) {
      sel.value = id;
      sel.dispatchEvent(new Event('change'));
    }
  }, 500);
}

function openEquipoModal() {
  ['eq-codigo', 'eq-descripcion', 'eq-fabricante', 'eq-modelo', 'eq-serie',
   'eq-rango', 'eq-resolucion', 'eq-tolerancia', 'eq-ubicacion'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  // Populate clients
  Clientes.list().then(data => {
    if (!data) return;
    const sel = document.getElementById('eq-cliente');
    if (sel) sel.innerHTML = '<option value="">— Sin cliente —</option>' +
      data.map(c => `<option value="${c.id}">${c.nombre}</option>`).join('');
  });
  openModal('equipo-modal');
}

async function saveEquipo() {
  const body = {
    codigo:      v('eq-codigo'),
    descripcion: v('eq-descripcion'),
    fabricante:  v('eq-fabricante'),
    modelo:      v('eq-modelo'),
    serie:       v('eq-serie'),
    rango:       v('eq-rango'),
    resolucion:  v('eq-resolucion'),
    tolerancia:  v('eq-tolerancia'),
    magnitud:    v('eq-magnitud'),
    ubicacion:   v('eq-ubicacion'),
    cliente_id:  v('eq-cliente') || null,
  };
  if (!body.codigo || !body.descripcion) { toast('Completa los campos requeridos', 'warn'); return; }
  const res = await Equipos.create(body);
  if (res?.ok) { toast('Equipo registrado exitosamente'); closeModal('equipo-modal'); loadEquipos(); }
  else toast(res?.error || 'Error al guardar', 'error');
}

// ══════════════════════════════════════════
//  PATRONES
// ══════════════════════════════════════════
async function deletePatron(id, codigo) {
  if (!confirm(`¿Dar de baja el patrón "${codigo}"?`)) return;
  const res = await Patrones.remove(id);
  if (res?.ok) { toast('Patrón dado de baja'); loadPatrones(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function loadPatrones() {
  const data = await Patrones.list();
  if (!data) return;
  const today = new Date().toISOString().substring(0, 10);
  const tbody = document.getElementById('tbl-patrones');
  if (!tbody) return;

  tbody.innerHTML = data.map(p => {
    let est = 'badge-green', etiq = 'Vigente';
    if (p.vencimiento && p.vencimiento < today)                     { est = 'badge-red';    etiq = 'Vencido';    }
    else if (p.vencimiento && p.vencimiento < addDays(today, 30)) { est = 'badge-yellow'; etiq = 'Por vencer'; }
    const vc = p.vencimiento
      ? `<span style="color:${p.vencimiento < today ? 'var(--danger)' : p.vencimiento < addDays(today, 30) ? 'var(--warn)' : 'var(--success)'}">${p.vencimiento}</span>`
      : '—';
    return `<tr>
      <td style="font-family:'DM Mono',monospace;font-size:12px;color:var(--accent)">${p.codigo}</td>
      <td>${p.descripcion}<br><span style="font-size:11px;color:var(--text3)">${p.fabricante || ''} ${p.modelo || ''}</span></td>
      <td>${p.magnitud || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${p.incertidumbre || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${p.n_certificado || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${vc}</td>
      <td><span class="badge ${est}"><span class="badge-dot"></span>${etiq}</span></td>
      <td><button class="btn-danger-sm" onclick="deletePatron(${p.id},'${(p.codigo||'').replace(/'/g,'')}')" title="Dar de baja">🗑️</button></td>
    </tr>`;
  }).join('') || '<tr><td colspan="8" style="text-align:center;color:var(--text3);padding:24px">Sin patrones registrados</td></tr>';
}

function openPatronModal() { openModal('patron-modal'); }

async function savePatron() {
  const body = {
    codigo:        v('pat-codigo'),
    descripcion:   v('pat-descripcion'),
    fabricante:    v('pat-fabricante'),
    modelo:        v('pat-modelo'),
    magnitud:      v('pat-magnitud'),
    incertidumbre: v('pat-incert'),
    n_certificado: v('pat-cert'),
    trazabilidad:  v('pat-trazab'),
    vencimiento:   v('pat-vencimiento'),
  };
  if (!body.codigo || !body.descripcion) { toast('Completa los campos requeridos', 'warn'); return; }
  const res = await Patrones.create(body);
  if (res?.ok) { toast('Patrón registrado'); closeModal('patron-modal'); loadPatrones(); }
  else toast(res?.error || 'Error', 'error');
}

// ══════════════════════════════════════════
//  CLIENTES
// ══════════════════════════════════════════
async function deleteCliente(id, nombre) {
  if (!confirm(`¿Eliminar el cliente "${nombre}"?`)) return;
  const res = await Clientes.remove(id);
  if (res?.ok) { toast('Cliente eliminado'); loadClientes(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function loadClientes() {
  const data = await Clientes.list();
  if (!data) return;
  const tbody = document.getElementById('tbl-clientes');
  if (!tbody) return;

  tbody.innerHTML = data.map(c => `
    <tr>
      <td style="font-family:'DM Mono',monospace;font-size:12px">${c.ruc || ''}</td>
      <td><b>${c.nombre}</b></td>
      <td>${c.contacto || ''}</td>
      <td>${c.email || ''}</td>
      <td style="text-align:center">${c.equipos_count || 0}</td>
      <td>
        <div style="display:flex;gap:4px">
          <button class="btn-sec btn-sm" onclick="editCliente(${c.id})">✏️ Editar</button>
          <button class="btn-danger-sm" onclick="deleteCliente(${c.id},'${(c.nombre||'').replace(/'/g,'')}')" title="Eliminar">🗑️</button>
        </div>
      </td>
    </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text3);padding:24px">Sin clientes registrados</td></tr>';
}

function openClienteModal() {
  ['cli-nombre', 'cli-ruc', 'cli-telefono', 'cli-contacto', 'cli-email', 'cli-direccion'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.value = '';
  });
  openModal('cliente-modal');
}

async function saveCliente() {
  const body = {
    nombre:    v('cli-nombre'),
    ruc:       v('cli-ruc'),
    contacto:  v('cli-contacto'),
    email:     v('cli-email'),
    telefono:  v('cli-telefono'),
    direccion: v('cli-direccion'),
  };
  if (!body.nombre) { toast('El nombre es requerido', 'warn'); return; }
  const res = await Clientes.create(body);
  if (res?.ok) { toast('Cliente registrado'); closeModal('cliente-modal'); loadClientes(); }
  else toast(res?.error || 'Error', 'error');
}

async function editCliente(id) {
  const c = await Clientes.get(id);
  if (!c) return;
  document.getElementById('cli-nombre').value    = c.nombre    || '';
  document.getElementById('cli-ruc').value       = c.ruc       || '';
  document.getElementById('cli-contacto').value  = c.contacto  || '';
  document.getElementById('cli-email').value     = c.email     || '';
  document.getElementById('cli-telefono').value  = c.telefono  || '';
  document.getElementById('cli-direccion').value = c.direccion || '';
  openModal('cliente-modal');
  // Change save button to update
  const btn = document.querySelector('#cliente-modal .btn-primary');
  if (btn) {
    btn.textContent = '💾 Actualizar';
    btn.onclick = async () => {
      const body = {
        nombre: v('cli-nombre'), ruc: v('cli-ruc'), contacto: v('cli-contacto'),
        email: v('cli-email'), telefono: v('cli-telefono'), direccion: v('cli-direccion'),
      };
      const res = await Clientes.update(id, body);
      if (res?.ok) { toast('Cliente actualizado'); closeModal('cliente-modal'); loadClientes(); }
      else toast(res?.error || 'Error', 'error');
      // Restore
      btn.textContent = '💾 Guardar';
      btn.onclick = saveCliente;
    };
  }
}

// ══════════════════════════════════════════
//  PERSONAL
// ══════════════════════════════════════════
async function deleteUsuario(id, nombre) {
  if (!confirm(`¿Dar de baja al usuario "${nombre}"?\nYa no podrá iniciar sesión.`)) return;
  const res = await Usuarios.remove(id);
  if (res?.ok) { toast('Usuario dado de baja'); loadPersonal(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function loadPersonal() {
  const data = await Usuarios.list();
  if (!data) return;
  const roles = { admin: 'Administrador', jefe: 'Jefe de Lab.', tecnico: 'Técnico' };
  const tbody = document.getElementById('tbl-personal');
  if (!tbody) return;

  tbody.innerHTML = data.map(u => `
    <tr>
      <td><b>${u.nombre}</b></td>
      <td style="font-family:'DM Mono',monospace;font-size:12px">${u.email}</td>
      <td><span class="badge badge-blue">${roles[u.rol] || u.rol}</span></td>
      <td>${u.laboratorio || ''}</td>
      <td><button class="btn-danger-sm" onclick="deleteUsuario(${u.id},'${(u.nombre||'').replace(/'/g,'')}')" title="Dar de baja">🗑️</button></td>
    </tr>`).join('') || '<tr><td colspan="5" style="text-align:center;color:var(--text3);padding:24px">Sin usuarios registrados</td></tr>';
}

// ══════════════════════════════════════════
//  CERTIFICADOS
// ══════════════════════════════════════════
async function loadCertificados() {
  const d = await Diagnosticos.list({ page: 1 });
  if (!d) return;
  const tbody = document.getElementById('tbl-certs');
  if (!tbody) return;

  tbody.innerHTML = (d.data || []).map(r => `
    <tr>
      <td style="font-family:'DM Mono',monospace;font-size:11px;color:var(--accent)">${r.n_certificado || '—'}</td>
      <td>${r.equipo_codigo || ''} — ${(r.equipo_desc || '').substring(0, 24)}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${(r.fecha_fin || '').substring(0, 10) || '—'}</td>
      <td>${r.cliente || ''}</td>
      <td>${resultBadge(r.resultado)}</td>
      <td><span class="badge ${r.enviado_email ? 'badge-green' : 'badge-yellow'}">${r.enviado_email ? '✓ Enviado' : 'Pendiente'}</span></td>
      <td><button class="btn-sec btn-sm" onclick="verPDFById(${r.id})">📄 PDF</button></td>
      <td><button class="btn-info btn-sm" onclick="openEmailModalById(${r.id})">📧</button></td>
      <td><button class="btn-danger-sm" onclick="deleteDiagnostico(${r.id},'${(r.n_certificado||'').replace(/'/g,'')}')" title="Eliminar">🗑️</button></td>
    </tr>`).join('') || '<tr><td colspan="9" style="text-align:center;color:var(--text3);padding:24px">Sin certificados</td></tr>';
}

// ══════════════════════════════════════════
//  ESTADÍSTICAS
// ══════════════════════════════════════════
async function loadEstadisticas() {
  const d = await Stats.get();
  if (!d) return;

  const total  = d.por_resultado.reduce((s, r) => s + r.total, 0) || 1;
  const colors = { conforme: 'var(--success)', no_conforme: 'var(--danger)', observacion: 'var(--warn)', pendiente: 'var(--text3)' };
  const labels = { conforme: 'Conforme', no_conforme: 'No conforme', observacion: 'Con observaciones', pendiente: 'Pendiente' };

  const container = document.getElementById('stats-content');
  if (!container) return;
  container.innerHTML = `
    <div class="two-col">
      <div class="inner-card">
        <div class="card-title" style="font-size:14px;margin-bottom:14px;">📊 Distribución por resultado</div>
        ${d.por_resultado.map(r => `
          <div style="margin-bottom:12px;">
            <div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:5px;">
              <span>${labels[r.resultado] || r.resultado}</span>
              <span style="color:${colors[r.resultado]||'var(--text)'};font-family:'DM Mono',monospace">${Math.round(r.total / total * 100)}% (${r.total})</span>
            </div>
            <div class="progress-bar"><div class="progress-fill" style="width:${Math.round(r.total / total * 100)}%;background:${colors[r.resultado] || 'var(--accent)'}"></div></div>
          </div>`).join('')}
      </div>
      <div class="inner-card">
        <div class="card-title" style="font-size:14px;margin-bottom:14px;">📅 Diagnósticos por mes</div>
        ${(() => {
          const maxM = Math.max(...d.por_mes.map(x => x.total), 1);
          return d.por_mes.slice(0, 8).map(m => `
            <div style="display:flex;align-items:center;gap:10px;margin-bottom:8px;">
              <div style="font-size:11px;color:var(--text3);width:64px;font-family:'DM Mono',monospace">${m.mes}</div>
              <div class="progress-bar" style="flex:1"><div class="progress-fill" style="width:${Math.round(m.total / maxM * 100)}%"></div></div>
              <div style="font-size:11px;font-family:'DM Mono',monospace;color:var(--accent);width:20px;text-align:right">${m.total}</div>
            </div>`).join('');
        })()}
      </div>
    </div>
    <div class="inner-card" style="margin-top:16px;">
      <div class="card-title" style="font-size:14px;margin-bottom:14px;">⚗️ Diagnósticos por magnitud</div>
      <div class="mag-grid">
        ${(() => {
          const maxP = Math.max(...d.por_magnitud.map(x => x.total), 1);
          const icons = { Presión: '🔵', Temperatura: '🌡️', Peso: '⚖️', Eléctrica: '⚡', Dimensional: '📏', pH: '🧪', Caudal: '💧', Vibración: '🔊' };
          return d.por_magnitud.map(m => `
            <div class="mag-item">
              <div class="mag-icon">${icons[m.magnitud] || '📊'}</div>
              <div class="mag-val">${m.total}</div>
              <div class="mag-lbl">${m.magnitud}</div>
              <div class="prog"><div class="prog-fill" style="width:${Math.round(m.total / maxP * 100)}%"></div></div>
            </div>`).join('');
        })()}
      </div>
    </div>`;
}

// ══════════════════════════════════════════
//  ALERTAS
// ══════════════════════════════════════════
async function loadAlertas() {
  const data = await Alertas.list();
  if (!data) return;

  const pending = data.filter(a => !a.resuelta);
  const badge   = document.getElementById('nb-alerts');
  const dot     = document.getElementById('alert-dot');
  if (badge) badge.textContent = pending.length;
  if (dot)   dot.style.display = pending.length > 0 ? 'block' : 'none';

  const icons = { vencimiento: '🚨', patron: '⚠️', no_conformidad: '📋', info: 'ℹ️' };
  const list  = document.getElementById('alertas-list');
  if (!list) return;

  list.innerHTML = data.map(a => `
    <div class="alert-item" style="${a.resuelta ? 'opacity:.45;' : ''}">
      <div class="alert-item-icon">${icons[a.tipo] || '📌'}</div>
      <div class="alert-item-content">
        <div class="alert-item-title">${a.titulo}</div>
        <div class="alert-item-msg">${a.mensaje || ''}</div>
        <div class="alert-item-time">${(a.creado || '').substring(0, 16)}</div>
      </div>
      <div style="display:flex;gap:6px;align-items:center">
        ${!a.resuelta
          ? `<button class="btn-sec btn-sm" onclick="resolveAlert(${a.id})">✓ Resolver</button>`
          : '<span class="badge badge-green">Resuelta</span>'}
        <button class="btn-danger-sm" onclick="deleteAlerta(${a.id})" title="Eliminar">🗑️</button>
      </div>
    </div>`).join('') || '<p style="color:var(--text3);padding:24px;text-align:center">Sin alertas activas 🎉</p>';
}

async function resolveAlert(id) {
  await Alertas.resolver(id);
  toast('Alerta resuelta');
  loadAlertas();
}

async function deleteAlerta(id) {
  if (!confirm('¿Eliminar esta alerta definitivamente?')) return;
  const res = await Alertas.remove(id);
  if (res?.ok) { toast('Alerta eliminada'); loadAlertas(); }
  else toast(res?.error || 'Error al eliminar', 'error');
}

async function resolveAll() {
  const data = await Alertas.list();
  if (!data) return;
  await Promise.all(data.filter(a => !a.resuelta).map(a => Alertas.resolver(a.id)));
  toast('Todas las alertas resueltas');
  loadAlertas();
}

// ══════════════════════════════════════════
//  AUDITORÍA
// ══════════════════════════════════════════
async function loadAuditoria() {
  const data = await Auditoria.list();
  if (!data) return;
  const badgeMap = { CREAR: 'badge-green', ACTUALIZAR: 'badge-blue', BAJA: 'badge-red', LOGIN: 'badge-yellow', LOGOUT: 'badge-yellow', FOTO: 'badge-blue', PDF: 'badge-blue', LECTURAS: 'badge-blue' };
  const tbody = document.getElementById('tbl-audit');
  if (!tbody) return;

  tbody.innerHTML = data.map(a => `
    <tr>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${(a.ts || '').substring(0, 16)}</td>
      <td>${a.usuario_nombre || '—'}</td>
      <td><span class="badge ${badgeMap[a.accion] || 'badge-blue'}">${a.accion || ''}</span></td>
      <td>${a.modulo || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px">${a.objeto || ''}</td>
      <td style="font-family:'DM Mono',monospace;font-size:11px;color:var(--text3)">${a.ip || ''}</td>
    </tr>`).join('') || '<tr><td colspan="6" style="text-align:center;color:var(--text3);padding:24px">Sin registros de auditoría</td></tr>';
}

// ══════════════════════════════════════════
//  BÚSQUEDA GLOBAL
// ══════════════════════════════════════════
const _searchIcons = { equipo: '🔧', diagnostico: '📋', cliente: '🏢' };
let _searchTimer;

function initGlobalSearch() {
  const input = document.getElementById('global-search');
  const drop  = document.getElementById('search-results');
  if (!input || !drop) return;

  input.addEventListener('input', () => {
    clearTimeout(_searchTimer);
    const q = input.value.trim();
    if (q.length < 2) { drop.style.display = 'none'; return; }
    _searchTimer = setTimeout(async () => {
      const results = await Search.query(q);
      if (!results?.length) { drop.style.display = 'none'; return; }
      drop.innerHTML = results.map(r =>
        `<div class="search-item" onclick="searchSelect('${r.tipo}',${r.id});this.closest('.search-drop').style.display='none'">
          ${_searchIcons[r.tipo] || '📌'} <b>${r.codigo}</b>
          <span style="color:var(--text3);font-size:11px"> ${r.descripcion || ''}</span>
        </div>`).join('');
      drop.style.display = 'block';
    }, 280);
  });

  document.addEventListener('click', e => {
    if (!e.target.closest('.search-wrap')) drop.style.display = 'none';
  });
}

function searchSelect(tipo, id) {
  if (tipo === 'equipo')       showPanel('equipos');
  else if (tipo === 'diagnostico') showPanel('historial');
  else if (tipo === 'cliente')     showPanel('clientes');
}

// ══════════════════════════════════════════
//  DOM HELPERS
// ══════════════════════════════════════════
function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val ?? '—';
}

// ══════════════════════════════════════════
//  INIT
// ══════════════════════════════════════════
document.addEventListener('DOMContentLoaded', () => {
  // Register panel loaders
  registerPanelLoader('dashboard',          loadDashboard);
  registerPanelLoader('historial',          loadHistorial);
  registerPanelLoader('equipos',            loadEquipos);
  registerPanelLoader('patrones',           loadPatrones);
  registerPanelLoader('clientes',           loadClientes);
  registerPanelLoader('personal',           loadPersonal);
  registerPanelLoader('certificados',       loadCertificados);
  registerPanelLoader('estadisticas',       loadEstadisticas);
  registerPanelLoader('alertas',            loadAlertas);
  registerPanelLoader('auditoria',          loadAuditoria);
  registerPanelLoader('nuevo-diagnostico',  initWizard);

  // Nav item click binding
  document.querySelectorAll('.nav-item[data-panel]').forEach(n => {
    n.addEventListener('click', () => showPanel(n.dataset.panel));
  });

  // Global search
  initGlobalSearch();

  // Initial panel — read from data attribute set by Flask
  const initialPanel = document.body.dataset.panel || 'dashboard';
  showPanel(initialPanel);
});
