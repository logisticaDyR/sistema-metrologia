"""
Diagnóstico Blueprint — wizard, lecturas, fotos, PDF
"""
import os, uuid, base64, json
from datetime import datetime, date
from flask import (Blueprint, request, session, jsonify,
                   render_template, current_app, send_file)
from calibpro_fixed.app.models.auth import login_required, log_action
from calibpro_fixed.app.models.database import query, execute, executemany, rows_to_list, row_to_dict

diagnostico_bp = Blueprint('diagnostico', __name__)

ALLOWED = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def _ext_ok(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED


def _gen_cert_number(magnitud):
    prefix = {
        'Presión': 'PRE', 'Temperatura': 'TER', 'Peso': 'BAL',
        'Eléctrica': 'ELE', 'pH': 'PHM', 'Caudal': 'CAU',
        'Dimensional': 'DIM', 'Vibración': 'VIB',
    }.get(magnitud, 'GEN')
    year = date.today().year
    last = query(
        "SELECT n_certificado FROM diagnosticos ORDER BY id DESC LIMIT 1", one=True)
    num = 1
    if last:
        try:
            num = int(last['n_certificado'].split('-')[-1]) + 1
        except Exception:
            pass
    return f"CERT-{year}-{prefix}-{num:04d}"


# ── LIST
@diagnostico_bp.route('/historial')
@login_required
def historial():
    return render_template('app.html', user=session, panel='historial')


@diagnostico_bp.route('/api/diagnosticos')
@login_required
def list_diagnosticos():
    page = int(request.args.get('page', 1))
    per  = 20
    off  = (page - 1) * per
    filtro = request.args.get('q', '')
    mag    = request.args.get('magnitud', '')

    where = "WHERE 1=1"
    params = []
    if filtro:
        where += " AND (e.codigo LIKE ? OR d.n_certificado LIKE ? OR c.nombre LIKE ?)"
        params += [f'%{filtro}%', f'%{filtro}%', f'%{filtro}%']
    if mag:
        where += " AND d.magnitud=?"
        params.append(mag)

    sql = f"""
        SELECT d.id, d.n_certificado, d.resultado, d.magnitud, d.fecha_fin, d.enviado_email,
               e.codigo as equipo_codigo, e.descripcion as equipo_desc,
               c.nombre as cliente,
               u.nombre as tecnico
        FROM diagnosticos d
        JOIN equipos e ON e.id=d.equipo_id
        LEFT JOIN clientes c ON c.id=e.cliente_id
        JOIN usuarios u ON u.id=d.tecnico_id
        {where}
        ORDER BY d.creado DESC LIMIT ? OFFSET ?
    """
    rows = rows_to_list(query(sql, params + [per, off]))

    total = query(f"SELECT COUNT(*) c FROM diagnosticos d JOIN equipos e ON e.id=d.equipo_id LEFT JOIN clientes c ON c.id=e.cliente_id {where}", params, one=True)['c']
    return jsonify({'data': rows, 'total': total, 'page': page})


# ── DELETE
@diagnostico_bp.route('/api/diagnosticos/<int:did>', methods=['DELETE'])
@login_required
def delete_diagnostico(did):
    row = query("SELECT n_certificado FROM diagnosticos WHERE id=?", (did,), one=True)
    if not row:
        return jsonify({'ok': False, 'error': 'No encontrado'}), 404
    cert = row['n_certificado']
    # Remove related records
    fotos = rows_to_list(query("SELECT filename FROM fotos WHERE diagnostico_id=?", (did,)))
    execute("DELETE FROM lecturas WHERE diagnostico_id=?", (did,))
    execute("DELETE FROM fotos WHERE diagnostico_id=?", (did,))
    execute("DELETE FROM diagnosticos WHERE id=?", (did,))
    # Remove photo files from disk
    import os as _os
    from flask import current_app as _app
    upload_folder = _app.config['UPLOAD_FOLDER']
    for f in fotos:
        fpath = _os.path.join(upload_folder, f['filename'])
        if _os.path.exists(fpath):
            try: _os.remove(fpath)
            except Exception: pass
    log_action('Diagnóstico', 'ELIMINAR', cert)
    return jsonify({'ok': True})


# ── CREATE (step-by-step wizard via JSON)
@diagnostico_bp.route('/api/diagnosticos', methods=['POST'])
@login_required
def create_diagnostico():
    data = request.get_json()
    equipo_id  = data.get('equipo_id')
    patron_id  = data.get('patron_id')
    magnitud   = data.get('magnitud', '')
    n_cert     = _gen_cert_number(magnitud)
    tecnico_id = session['user_id']

    did = execute("""
        INSERT INTO diagnosticos(n_certificado,equipo_id,patron_id,tecnico_id,procedimiento,magnitud,unidad,
            observaciones,temp_inicio,temp_fin,humedad_inicio,humedad_fin,presion_atm,
            fecha_inicio,prox_calibracion)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,datetime('now'),?)
    """, (
        n_cert, equipo_id, patron_id, tecnico_id,
        data.get('procedimiento'), magnitud, data.get('unidad'),
        data.get('observaciones'),
        data.get('temp_inicio'), data.get('temp_fin'),
        data.get('humedad_inicio'), data.get('humedad_fin'),
        data.get('presion_atm'),
        data.get('prox_calibracion'),
    ))

    log_action('Diagnóstico', 'CREAR', n_cert)
    return jsonify({'ok': True, 'id': did, 'n_certificado': n_cert})


# ── UPDATE result / conclusion
@diagnostico_bp.route('/api/diagnosticos/<int:did>', methods=['PUT'])
@login_required
def update_diagnostico(did):
    data = request.get_json()
    execute("""
        UPDATE diagnosticos SET
            resultado=?, dictamen=?, observaciones=?,
            estado_visual=?, fecha_fin=datetime('now'),
            prox_calibracion=?
        WHERE id=?
    """, (
        data.get('resultado'), data.get('dictamen'),
        data.get('observaciones'), data.get('estado_visual'),
        data.get('prox_calibracion'), did
    ))
    log_action('Diagnóstico', 'ACTUALIZAR', str(did))
    return jsonify({'ok': True})


# ── GET single
@diagnostico_bp.route('/api/diagnosticos/<int:did>')
@login_required
def get_diagnostico(did):
    row = query("""
        SELECT d.*, e.codigo equipo_codigo, e.descripcion equipo_desc,
               e.fabricante, e.modelo, e.serie, e.rango, e.resolucion, e.tolerancia, e.ubicacion,
               c.nombre as cliente_nombre, c.email as cliente_email,
               u.nombre as tecnico_nombre,
               p.codigo as patron_codigo, p.descripcion as patron_desc,
               p.incertidumbre as patron_incert, p.n_certificado as patron_cert
        FROM diagnosticos d
        JOIN equipos e ON e.id=d.equipo_id
        LEFT JOIN clientes c ON c.id=e.cliente_id
        JOIN usuarios u ON u.id=d.tecnico_id
        LEFT JOIN patrones p ON p.id=d.patron_id
        WHERE d.id=?
    """, (did,), one=True)

    if not row:
        return jsonify({'error': 'No encontrado'}), 404

    lecturas = rows_to_list(query(
        "SELECT * FROM lecturas WHERE diagnostico_id=? ORDER BY ciclo,punto", (did,)))

    fotos = rows_to_list(query(
        "SELECT id,label,filename,tipo,creado FROM fotos WHERE diagnostico_id=? ORDER BY id", (did,)))

    result = dict(row)
    result['lecturas'] = lecturas
    result['fotos'] = fotos
    return jsonify(result)


# ── LECTURAS save batch
@diagnostico_bp.route('/api/diagnosticos/<int:did>/lecturas', methods=['POST'])
@login_required
def save_lecturas(did):
    data = request.get_json()
    lecturas = data.get('lecturas', [])
    # Delete old and reinsert
    execute("DELETE FROM lecturas WHERE diagnostico_id=?", (did,))
    rows = []
    for l in lecturas:
        rows.append((
            did,
            l.get('ciclo', 1), l.get('punto', 1),
            l.get('valor_nominal'), l.get('porcentaje_rango'),
            l.get('lectura_ebp'), l.get('lectura_patron'),
            l.get('desviacion'), l.get('error_pct'),
            l.get('incertidumbre'),
        ))
    executemany("""
        INSERT INTO lecturas(diagnostico_id,ciclo,punto,valor_nominal,porcentaje_rango,
            lectura_ebp,lectura_patron,desviacion,error_pct,incertidumbre)
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """, rows)
    log_action('Diagnóstico', 'LECTURAS', str(did), f'{len(rows)} filas')
    return jsonify({'ok': True, 'count': len(rows)})


# ── PHOTOS upload (multipart OR base64)
@diagnostico_bp.route('/api/diagnosticos/<int:did>/fotos', methods=['POST'])
@login_required
def upload_foto(did):
    folder = current_app.config['UPLOAD_FOLDER']
    saved  = []

    # ── multipart files
    if request.files:
        for key, f in request.files.items():
            if f and _ext_ok(f.filename):
                ext      = f.filename.rsplit('.', 1)[1].lower()
                fname    = f"{uuid.uuid4().hex}.{ext}"
                fpath    = os.path.join(folder, fname)
                f.save(fpath)
                size     = os.path.getsize(fpath)
                label    = request.form.get(f'label_{key}', key)
                tipo     = request.form.get(f'tipo_{key}', 'requerida')
                fid = execute(
                    "INSERT INTO fotos(diagnostico_id,filename,label,tipo,size_bytes) VALUES(?,?,?,?,?)",
                    (did, fname, label, tipo, size))
                saved.append({'id': fid, 'filename': fname, 'label': label})

    # ── base64 JSON payload
    elif request.is_json:
        photos = request.get_json().get('photos', [])
        for p in photos:
            try:
                header, b64 = p['dataUrl'].split(',', 1)
                ext   = 'jpg'
                if 'png' in header:  ext = 'png'
                elif 'gif' in header: ext = 'gif'
                fname = f"{uuid.uuid4().hex}.{ext}"
                fpath = os.path.join(folder, fname)
                with open(fpath, 'wb') as fp:
                    fp.write(base64.b64decode(b64))
                size  = os.path.getsize(fpath)
                fid   = execute(
                    "INSERT INTO fotos(diagnostico_id,filename,label,tipo,size_bytes) VALUES(?,?,?,?,?)",
                    (did, fname, p.get('label','Foto'), p.get('tipo','requerida'), size))
                saved.append({'id': fid, 'filename': fname, 'label': p.get('label')})
            except Exception as e:
                pass  # skip bad images

    log_action('Diagnóstico', 'FOTO', str(did), f'{len(saved)} fotos')
    return jsonify({'ok': True, 'saved': saved})


# ── Serve a photo
@diagnostico_bp.route('/fotos/<filename>')
@login_required
def serve_foto(filename):
    folder = current_app.config['UPLOAD_FOLDER']
    path   = os.path.join(folder, filename)
    if not os.path.exists(path):
        return 'Not found', 404
    return send_file(path)


# ── DELETE photo
@diagnostico_bp.route('/api/fotos/<int:fid>', methods=['DELETE'])
@login_required
def delete_foto(fid):
    row = query("SELECT filename FROM fotos WHERE id=?", (fid,), one=True)
    if row:
        folder = current_app.config['UPLOAD_FOLDER']
        fpath  = os.path.join(folder, row['filename'])
        if os.path.exists(fpath):
            os.remove(fpath)
        execute("DELETE FROM fotos WHERE id=?", (fid,))
    return jsonify({'ok': True})
