"""
Clientes Blueprint
"""
from flask import Blueprint, request, jsonify
from app.models.auth import login_required, log_action
from app.models.database import query, execute, rows_to_list, row_to_dict

clientes_bp = Blueprint('clientes', __name__)


@clientes_bp.route('/api/clientes')
@login_required
def list_clientes():
    rows = rows_to_list(query("""
        SELECT c.*, COUNT(e.id) as equipos_count
        FROM clientes c
        LEFT JOIN equipos e ON e.cliente_id=c.id AND e.activo=1
        WHERE c.activo=1
        GROUP BY c.id
        ORDER BY c.nombre
    """))
    return jsonify(rows)


@clientes_bp.route('/api/clientes/<int:cid>')
@login_required
def get_cliente(cid):
    row = row_to_dict(query("SELECT * FROM clientes WHERE id=?", (cid,), one=True))
    return jsonify(row) if row else ('', 404)


@clientes_bp.route('/api/clientes', methods=['POST'])
@login_required
def create_cliente():
    d = request.get_json()
    cid = execute(
        "INSERT INTO clientes(nombre,ruc,contacto,email,telefono,direccion) VALUES(?,?,?,?,?,?)",
        (d.get('nombre'), d.get('ruc'), d.get('contacto'),
         d.get('email'), d.get('telefono'), d.get('direccion')))
    log_action('Clientes', 'CREAR', d.get('nombre'))
    return jsonify({'ok': True, 'id': cid})


@clientes_bp.route('/api/clientes/<int:cid>', methods=['PUT'])
@login_required
def update_cliente(cid):
    d = request.get_json()
    execute("""
        UPDATE clientes SET nombre=?,ruc=?,contacto=?,email=?,telefono=?,direccion=?
        WHERE id=?
    """, (d.get('nombre'), d.get('ruc'), d.get('contacto'),
          d.get('email'), d.get('telefono'), d.get('direccion'), cid))
    log_action('Clientes', 'ACTUALIZAR', str(cid))
    return jsonify({'ok': True})


@clientes_bp.route('/api/clientes/<int:cid>', methods=['DELETE'])
@login_required
def delete_cliente(cid):
    execute("UPDATE clientes SET activo=0 WHERE id=?", (cid,))
    log_action('Clientes', 'BAJA', str(cid))
    return jsonify({'ok': True})
