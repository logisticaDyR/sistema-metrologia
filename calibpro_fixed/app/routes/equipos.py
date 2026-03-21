"""
Equipos Blueprint
"""
from flask import Blueprint, request, jsonify, session
from app.models.auth import login_required, log_action
from app.models.database import query, execute, rows_to_list, row_to_dict

equipos_bp = Blueprint('equipos', __name__)


@equipos_bp.route('/api/equipos')
@login_required
def list_equipos():
    q   = request.args.get('q', '')
    mag = request.args.get('magnitud', '')
    where = "WHERE e.activo=1"
    params = []
    if q:
        where += " AND (e.codigo LIKE ? OR e.descripcion LIKE ?)"
        params += [f'%{q}%', f'%{q}%']
    if mag:
        where += " AND e.magnitud=?"
        params.append(mag)

    rows = rows_to_list(query(f"""
        SELECT e.*, c.nombre as cliente_nombre,
               MAX(d.fecha_fin) as ultima_calibracion,
               MAX(d.prox_calibracion) as prox_calibracion,
               MAX(d.resultado) as ultimo_resultado
        FROM equipos e
        LEFT JOIN clientes c ON c.id=e.cliente_id
        LEFT JOIN diagnosticos d ON d.equipo_id=e.id
        {where}
        GROUP BY e.id
        ORDER BY e.codigo
    """, params))
    return jsonify(rows)


@equipos_bp.route('/api/equipos/<int:eid>')
@login_required
def get_equipo(eid):
    row = row_to_dict(query(
        "SELECT e.*, c.nombre as cliente_nombre FROM equipos e LEFT JOIN clientes c ON c.id=e.cliente_id WHERE e.id=?",
        (eid,), one=True))
    if not row:
        return jsonify({'error': 'No encontrado'}), 404
    historico = rows_to_list(query(
        "SELECT id,n_certificado,resultado,fecha_fin FROM diagnosticos WHERE equipo_id=? ORDER BY fecha_fin DESC",
        (eid,)))
    row['historico'] = historico
    return jsonify(row)


@equipos_bp.route('/api/equipos', methods=['POST'])
@login_required
def create_equipo():
    d = request.get_json()
    eid = execute("""
        INSERT INTO equipos(codigo,descripcion,fabricante,modelo,serie,rango,
            resolucion,tolerancia,magnitud,ubicacion,cliente_id)
        VALUES(?,?,?,?,?,?,?,?,?,?,?)
    """, (d.get('codigo'), d.get('descripcion'), d.get('fabricante'), d.get('modelo'),
          d.get('serie'), d.get('rango'), d.get('resolucion'), d.get('tolerancia'),
          d.get('magnitud'), d.get('ubicacion'), d.get('cliente_id')))
    log_action('Equipos', 'CREAR', d.get('codigo'))
    return jsonify({'ok': True, 'id': eid})


@equipos_bp.route('/api/equipos/<int:eid>', methods=['PUT'])
@login_required
def update_equipo(eid):
    d = request.get_json()
    execute("""
        UPDATE equipos SET descripcion=?,fabricante=?,modelo=?,serie=?,rango=?,
            resolucion=?,tolerancia=?,magnitud=?,ubicacion=?,cliente_id=?
        WHERE id=?
    """, (d.get('descripcion'), d.get('fabricante'), d.get('modelo'), d.get('serie'),
          d.get('rango'), d.get('resolucion'), d.get('tolerancia'), d.get('magnitud'),
          d.get('ubicacion'), d.get('cliente_id'), eid))
    log_action('Equipos', 'ACTUALIZAR', str(eid))
    return jsonify({'ok': True})


@equipos_bp.route('/api/equipos/<int:eid>', methods=['DELETE'])
@login_required
def delete_equipo(eid):
    execute("UPDATE equipos SET activo=0 WHERE id=?", (eid,))
    log_action('Equipos', 'BAJA', str(eid))
    return jsonify({'ok': True})
