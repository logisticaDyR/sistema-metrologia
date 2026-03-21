/**
 * Tatronics — API Layer
 * Centralizes all fetch() calls to the Flask backend.
 */
'use strict';

// ── Base fetch helper ──────────────────────────────────────────────────────
async function api(method, url, body) {
  const opts = { method, headers: {} };
  if (body) {
    opts.headers['Content-Type'] = 'application/json';
    opts.body = JSON.stringify(body);
  }
  try {
    const res = await fetch(url, opts);
    if (res.status === 401) { window.location = '/login'; return null; }
    return await res.json().catch(() => null);
  } catch (err) {
    console.error('API error:', method, url, err);
    return null;
  }
}

// ── Auth ───────────────────────────────────────────────────────────────────
const Auth = {
  me:     ()        => api('GET',  '/api/usuarios/me'),
  login:  (email, password) => api('POST', '/login', { email, password }),
  logout: ()        => window.location = '/auth/logout',
};

// ── Dashboard ──────────────────────────────────────────────────────────────
const Dashboard = {
  stats: () => api('GET', '/api/dashboard/stats'),
};

// ── Equipos ────────────────────────────────────────────────────────────────
const Equipos = {
  list:   (q = '', mag = '')   => api('GET', `/api/equipos?q=${encodeURIComponent(q)}&magnitud=${encodeURIComponent(mag)}`),
  get:    (id)                 => api('GET', `/api/equipos/${id}`),
  create: (data)               => api('POST', '/api/equipos', data),
  update: (id, data)           => api('PUT',  `/api/equipos/${id}`, data),
  remove: (id)                 => api('DELETE', `/api/equipos/${id}`),
};

// ── Diagnósticos ──────────────────────────────────────────────────────────
const Diagnosticos = {
  list:          (params = {}) => api('GET', `/api/diagnosticos?${new URLSearchParams(params)}`),
  get:           (id)          => api('GET', `/api/diagnosticos/${id}`),
  create:        (data)        => api('POST', '/api/diagnosticos', data),
  update:        (id, data)    => api('PUT',  `/api/diagnosticos/${id}`, data),
  saveLecturas:  (id, lecturas)=> api('POST', `/api/diagnosticos/${id}/lecturas`, { lecturas }),
  savePhotos:    (id, photos)  => api('POST', `/api/diagnosticos/${id}/fotos`, { photos }),
  deletePhoto:   (fid)         => api('DELETE', `/api/fotos/${fid}`),
  getPDF:        (id)          => `/api/diagnosticos/${id}/pdf`,
  sendEmail:     (id, data)    => api('POST',   `/api/diagnosticos/${id}/email`, data),
  remove:        (id)          => api('DELETE', `/api/diagnosticos/${id}`),
};

// ── Clientes ───────────────────────────────────────────────────────────────
const Clientes = {
  list:   ()      => api('GET',    '/api/clientes'),
  get:    (id)    => api('GET',    `/api/clientes/${id}`),
  create: (data)  => api('POST',   '/api/clientes', data),
  update: (id, d) => api('PUT',    `/api/clientes/${id}`, d),
  remove: (id)    => api('DELETE', `/api/clientes/${id}`),
};

// ── Patrones ───────────────────────────────────────────────────────────────
const Patrones = {
  list:   ()     => api('GET',    '/api/patrones'),
  create: (data) => api('POST',   '/api/patrones', data),
  remove: (id)   => api('DELETE', `/api/patrones/${id}`),
};

// ── Usuarios ───────────────────────────────────────────────────────────────
const Usuarios = {
  list:   ()   => api('GET',    '/api/usuarios'),
  remove: (id) => api('DELETE', `/api/usuarios/${id}`),
};

// ── Alertas ────────────────────────────────────────────────────────────────
const Alertas = {
  list:     ()    => api('GET',    '/api/alertas'),
  resolver: (id)  => api('POST',   `/api/alertas/${id}/resolver`),
  remove:   (id)  => api('DELETE', `/api/alertas/${id}`),
};

// ── Auditoría ──────────────────────────────────────────────────────────────
const Auditoria = {
  list: () => api('GET', '/api/audit'),
};

// ── Estadísticas ──────────────────────────────────────────────────────────
const Stats = {
  get: () => api('GET', '/api/estadisticas'),
};

// ── Búsqueda global ────────────────────────────────────────────────────────
const Search = {
  query: (q) => api('GET', `/api/search?q=${encodeURIComponent(q)}`),
};
