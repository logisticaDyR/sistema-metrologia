"""
General API Blueprint — patrones, usuarios, búsqueda global
"""
from flask import Blueprint, request, jsonify, session
from app.models.auth import login_required, log_action
from app.models.database import query, execute, rows_to_list, row_to_dict

api_bp = Blueprint('api', __name__)


@api_bp.route('/patrones')
@login_required
def list_patrones():
    rows = rows_to_list(query(
        "SELECT * FROM patrones WHERE activo=1 ORDER BY codigo"))
    return jsonify(rows)


@api_bp.route('/patrones', methods=['POST'])
@login_required
def create_patron():
    d = request.get_json()
    pid = execute("""
        INSERT INTO patrones(codigo,descripcion,fabricante,modelo,serie,magnitud,
            incertidumbre,n_certificado,trazabilidad,vencimiento)
        VALUES(?,?,?,?,?,?,?,?,?,?)
    """, (d.get('codigo'), d.get('descripcion'), d.get('fabricante'), d.get('modelo'),
          d.get('serie'), d.get('magnitud'), d.get('incertidumbre'),
          d.get('n_certificado'), d.get('trazabilidad'), d.get('vencimiento')))
    log_action('Patrones', 'CREAR', d.get('codigo'))
    return jsonify({'ok': True, 'id': pid})


@api_bp.route('/patrones/<int:pid>', methods=['DELETE'])
@login_required
def delete_patron(pid):
    execute("UPDATE patrones SET activo=0 WHERE id=?", (pid,))
    log_action('Patrones', 'BAJA', str(pid))
    return jsonify({'ok': True})


@api_bp.route('/usuarios/me')
@login_required
def me():
    return jsonify({
        'id':          session.get('user_id'),
        'nombre':      session.get('user_nombre'),
        'email':       session.get('user_email'),
        'rol':         session.get('user_rol'),
        'laboratorio': session.get('laboratorio'),
    })


@api_bp.route('/usuarios')
@login_required
def list_usuarios():
    rows = rows_to_list(query(
        "SELECT id,nombre,email,rol,laboratorio,activo,creado FROM usuarios WHERE activo=1"))
    return jsonify(rows)


@api_bp.route('/usuarios/<int:uid>', methods=['DELETE'])
@login_required
def delete_usuario(uid):
    from flask import session as _sess
    if uid == _sess.get('user_id'):
        return jsonify({'ok': False, 'error': 'No puedes eliminar tu propio usuario'}), 400
    execute("UPDATE usuarios SET activo=0 WHERE id=?", (uid,))
    log_action('Personal', 'BAJA', str(uid))
    return jsonify({'ok': True})


@api_bp.route('/search')
@login_required
def global_search():
    q = request.args.get('q', '').strip()
    if not q:
        return jsonify([])
    pat = f'%{q}%'
    results = []

    # Equipment
    for r in rows_to_list(query(
            "SELECT id,'equipo' tipo,codigo,descripcion FROM equipos WHERE activo=1 AND (codigo LIKE ? OR descripcion LIKE ?) LIMIT 5",
            (pat, pat))):
        results.append(r)

    # Diagnostics
    for r in rows_to_list(query(
            "SELECT id,'diagnostico' tipo,n_certificado as codigo,magnitud as descripcion FROM diagnosticos WHERE n_certificado LIKE ? LIMIT 5",
            (pat,))):
        results.append(r)

    # Clients
    for r in rows_to_list(query(
            "SELECT id,'cliente' tipo,nombre as codigo,ruc as descripcion FROM clientes WHERE activo=1 AND (nombre LIKE ? OR ruc LIKE ?) LIMIT 3",
            (pat, pat))):
        results.append(r)

    return jsonify(results)
