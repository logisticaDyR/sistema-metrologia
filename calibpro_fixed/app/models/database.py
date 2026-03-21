"""
Tatronics — Database Layer (SQLite via sqlite3)
All CRUD helpers live here as simple functions.
"""
import sqlite3
import hashlib
import os
from datetime import datetime, date


# ──────────────────────────────────────────
#  CONNECTION
# ──────────────────────────────────────────
_DB_PATH = None

def get_db(path=None):
    p = path or _DB_PATH
    conn = sqlite3.connect(p)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.execute("PRAGMA journal_mode = WAL")
    return conn


def init_db(path):
    global _DB_PATH
    _DB_PATH = path
    conn = get_db(path)
    _create_tables(conn)
    _seed_data(conn)
    conn.close()


# ──────────────────────────────────────────
#  SCHEMA
# ──────────────────────────────────────────
SCHEMA = """
CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    email       TEXT NOT NULL UNIQUE,
    password    TEXT NOT NULL,
    rol         TEXT NOT NULL DEFAULT 'tecnico',  -- admin | jefe | tecnico
    laboratorio TEXT DEFAULT 'Lab. Central',
    activo      INTEGER DEFAULT 1,
    creado      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS clientes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    ruc         TEXT,
    contacto    TEXT,
    email       TEXT,
    telefono    TEXT,
    direccion   TEXT,
    activo      INTEGER DEFAULT 1,
    creado      TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS equipos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT NOT NULL UNIQUE,
    descripcion     TEXT NOT NULL,
    fabricante      TEXT,
    modelo          TEXT,
    serie           TEXT,
    rango           TEXT,
    resolucion      TEXT,
    tolerancia      TEXT,
    magnitud        TEXT,
    ubicacion       TEXT,
    cliente_id      INTEGER REFERENCES clientes(id),
    activo          INTEGER DEFAULT 1,
    creado          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS patrones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    codigo          TEXT NOT NULL UNIQUE,
    descripcion     TEXT NOT NULL,
    fabricante      TEXT,
    modelo          TEXT,
    serie           TEXT,
    magnitud        TEXT,
    incertidumbre   TEXT,
    n_certificado   TEXT,
    trazabilidad    TEXT,
    vencimiento     TEXT,
    activo          INTEGER DEFAULT 1,
    creado          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS diagnosticos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    n_certificado   TEXT UNIQUE,
    equipo_id       INTEGER NOT NULL REFERENCES equipos(id),
    patron_id       INTEGER REFERENCES patrones(id),
    tecnico_id      INTEGER NOT NULL REFERENCES usuarios(id),
    procedimiento   TEXT,
    magnitud        TEXT,
    unidad          TEXT,
    resultado       TEXT DEFAULT 'pendiente',  -- conforme|no_conforme|observacion|pendiente
    dictamen        TEXT,
    estado_visual   TEXT,
    observaciones   TEXT,
    temp_inicio     REAL, temp_fin     REAL,
    humedad_inicio  REAL, humedad_fin  REAL,
    presion_atm     REAL,
    fecha_inicio    TEXT DEFAULT (datetime('now')),
    fecha_fin       TEXT,
    prox_calibracion TEXT,
    enviado_email   INTEGER DEFAULT 0,
    creado          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS lecturas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    diagnostico_id  INTEGER NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    ciclo           INTEGER DEFAULT 1,
    punto           INTEGER DEFAULT 1,
    valor_nominal   REAL,
    porcentaje_rango REAL,
    lectura_ebp     REAL,
    lectura_patron  REAL,
    desviacion      REAL,
    error_pct       REAL,
    incertidumbre   REAL
);

CREATE TABLE IF NOT EXISTS fotos (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    diagnostico_id  INTEGER NOT NULL REFERENCES diagnosticos(id) ON DELETE CASCADE,
    filename        TEXT NOT NULL,
    label           TEXT,
    tipo            TEXT DEFAULT 'referencia',  -- requerida|adicional|no_conformidad
    mime_type       TEXT DEFAULT 'image/jpeg',
    size_bytes      INTEGER,
    creado          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS alertas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo            TEXT NOT NULL,   -- vencimiento|no_conformidad|patron|info
    titulo          TEXT NOT NULL,
    mensaje         TEXT,
    entidad         TEXT,
    entidad_id      INTEGER,
    resuelta        INTEGER DEFAULT 0,
    creado          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS audit_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER REFERENCES usuarios(id),
    accion      TEXT NOT NULL,
    modulo      TEXT,
    objeto      TEXT,
    detalle     TEXT,
    ip          TEXT,
    ts          TEXT DEFAULT (datetime('now'))
);
"""


def _create_tables(conn):
    conn.executescript(SCHEMA)
    conn.commit()


def _hash(pw):
    return hashlib.sha256(pw.encode()).hexdigest()


def _seed_data(conn):
    # Only seed if no users exist
    row = conn.execute("SELECT COUNT(*) as c FROM usuarios").fetchone()
    if row['c'] > 0:
        return

    # Users
    users = [
        ('Ing. Carlos Ruiz',    'admin@tatronicsperu.com',    _hash('admin123'),  'admin',  'Lab. Central'),
        ('Ing. Paola Torres',   'p.torres@tatronicsperu.com', _hash('tecnico123'), 'tecnico','Lab. Central'),
        ('Ing. Patricia Vega',  'jefe@tatronicsperu.com',     _hash('jefe123'),   'jefe',   'Lab. Central'),
    ]
    conn.executemany(
        "INSERT INTO usuarios(nombre,email,password,rol,laboratorio) VALUES(?,?,?,?,?)", users)

    # Clients
    clientes = [
        ('Minera Andes S.A.',  '20512345678', 'Ing. Luis Zapata',  'l.zapata@mineraandes.pe',  '01-234-5678', 'Av. Industrial 450, Lima'),
        ('Farma Norte S.A.',   '20498712300', 'Ing. Rosa Medina',  'r.medina@farmanorte.pe',   '01-876-5432', 'Calle Los Álamos 120, Lima'),
        ('Petro Química Norte', '20534100200', 'Ing. Jorge Salas', 'j.salas@petroquimica.pe',  '01-456-7890', 'Zona Industrial Norte, Trujillo'),
        ('Laboratorio interno','00000000000', 'Admin Tatronics',   'admin@tatronicsperu.com',  '',            'Sede Principal'),
    ]
    conn.executemany(
        "INSERT INTO clientes(nombre,ruc,contacto,email,telefono,direccion) VALUES(?,?,?,?,?,?)", clientes)

    # Equipment
    equipos = [
        ('MAN-0085','Manómetro digital de proceso','WIKA','S-10 Series','WK-2024-003851','0 — 10 bar','0.001 bar','±0.5% FS','Presión','Planta 3 — Línea B',1),
        ('MAN-0084','Manómetro Bourdon industrial','WIKA','232.50','WK-2022-0084','0 — 16 bar','0.02 bar','±1.6% FS','Presión','Planta 2',1),
        ('BAL-0042','Balanza analítica de precisión','Sartorius','Entris224','SAR-2021-0042','0 — 220 g','0.0001 g','±0.0002 g','Peso','Lab. QC',2),
        ('TER-0118','Termómetro de referencia Pt100','Fluke','1524','FL-1524-7823','-200 — 660 °C','0.001 °C','±0.04 °C','Temperatura','Lab. Central',4),
        ('PHM-0033','pHmetro de laboratorio','Mettler Toledo','Seven Excellence','MT-SE-2023-0033','0 — 14 pH','0.001 pH','±0.002 pH','pH','Lab. Química',2),
        ('MUL-0011','Multímetro de precisión','Fluke','8846A','FL-8846-0011','0 — 1000 V','0.0001 V','±0.0035%','Eléctrica','Lab. Central',4),
        ('CAU-0007','Caudalímetro ultrasónico','Endress+Hauser','Prosonic Flow','EH-PF-2022-007','0 — 100 m³/h','0.1 m³/h','±0.5%','Caudal','Planta 1',3),
    ]
    conn.executemany(
        "INSERT INTO equipos(codigo,descripcion,fabricante,modelo,serie,rango,resolucion,tolerancia,magnitud,ubicacion,cliente_id) VALUES(?,?,?,?,?,?,?,?,?,?,?)", equipos)

    # Patrones
    patrones = [
        ('P-REF-001','Juego de pesas OIML F1','Mettler Toledo','—','MT-F1-2024-001','Peso','U=0.006 mg (k=2)','RNM-2025-0481','RNM — Perú','2026-10-15'),
        ('P-REF-003','Manómetro patrón digital','Fluke','700G31','FL-700G31-003','Presión','U=0.005%FS (k=2)','RNM-2025-0392','RNM — Perú','2026-03-20'),
        ('P-REF-005','Calibrador de temperatura de referencia','Fluke','9142','FL-9142-005','Temperatura','U=0.04°C (k=2)','RNM-2025-0612','RNM — Perú','2026-11-30'),
        ('P-REF-007','Calibrador multifunción eléctrico','Fluke','5522A','FL-5522A-007','Eléctrica','U=0.0015% (k=2)','RNM-2025-0744','RNM — Perú','2026-08-20'),
    ]
    conn.executemany(
        "INSERT INTO patrones(codigo,descripcion,fabricante,modelo,serie,magnitud,incertidumbre,n_certificado,trazabilidad,vencimiento) VALUES(?,?,?,?,?,?,?,?,?,?)", patrones)

    # Sample diagnostico
    conn.execute("""
        INSERT INTO diagnosticos(n_certificado,equipo_id,patron_id,tecnico_id,procedimiento,magnitud,unidad,
            resultado,dictamen,observaciones,temp_inicio,temp_fin,humedad_inicio,humedad_fin,presion_atm,
            fecha_inicio,fecha_fin,prox_calibracion,enviado_email)
        VALUES('CERT-2026-PRE-0084',2,2,1,'TP-PRE-001','Presión','bar',
            'conforme','Apto para uso sin restricciones',
            'El instrumento cumple especificaciones.',
            22.4,23.1,58.0,60.0,1013.2,
            '2026-03-07 09:00','2026-03-07 11:30','2027-03-07',1)
    """)
    diag_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
    lecturas = [
        (diag_id,1,1, 0.0,   0,   0.002, 0.000, 0.002, 0.02, 0.052),
        (diag_id,1,2, 2.5,  25,   2.512, 2.499, 0.013, 0.13, 0.052),
        (diag_id,1,3, 5.0,  50,   5.031, 5.000, 0.031, 0.31, 0.052),
        (diag_id,1,4, 7.5,  75,   7.528, 7.501, 0.027, 0.27, 0.052),
        (diag_id,1,5,10.0, 100,  10.044, 9.998, 0.046, 0.46, 0.052),
    ]
    conn.executemany(
        "INSERT INTO lecturas(diagnostico_id,ciclo,punto,valor_nominal,porcentaje_rango,lectura_ebp,lectura_patron,desviacion,error_pct,incertidumbre) VALUES(?,?,?,?,?,?,?,?,?,?)",
        lecturas)

    # Sample alerts
    alertas = [
        ('vencimiento','BAL-0042 — Calibración VENCIDA','La balanza Sartorius superó su fecha de calibración el 05/03/2026.','equipo',3),
        ('patron','P-REF-003 — Patrón vence en 12 días','El manómetro patrón Fluke 700G31 vence el 20/03/2026.','patron',2),
        ('no_conformidad','No conformidad abierta — BAL-0039','Desviación de +0.42g detectada (límite ±0.2g).','diagnostico',1),
        ('info','Actualización de procedimiento TP-TEM-002','Revisado según ISO 1770-1:2024.','sistema',0),
    ]
    conn.executemany(
        "INSERT INTO alertas(tipo,titulo,mensaje,entidad,entidad_id) VALUES(?,?,?,?,?)", alertas)

    conn.commit()
    print("[DB] Seed data inserted successfully.")


# ──────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────

def query(sql, params=(), one=False):
    conn = get_db()
    cur = conn.execute(sql, params)
    result = cur.fetchone() if one else cur.fetchall()
    conn.close()
    return result

def execute(sql, params=()):
    conn = get_db()
    cur = conn.execute(sql, params)
    last_id = cur.lastrowid
    conn.commit()
    conn.close()
    return last_id

def executemany(sql, params_list):
    conn = get_db()
    conn.executemany(sql, params_list)
    conn.commit()
    conn.close()

def row_to_dict(row):
    if row is None:
        return None
    return dict(row)

def rows_to_list(rows):
    return [dict(r) for r in rows]
