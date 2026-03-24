"""
Dashboard Blueprint
"""
from flask import Blueprint, render_template, session, jsonify
from calibpro_fixed.app.models.auth import login_required
from calibpro_fixed.app.models.database import query, rows_to_list

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/dashboard')
@login_required
def index():
    return render_template('app.html',
                           user=session,
                           panel='dashboard')


@dashboard_bp.route('/api/dashboard/stats')
@login_required
def stats():
    diag_mes   = query("SELECT COUNT(*) c FROM diagnosticos WHERE strftime('%Y-%m', creado)=strftime('%Y-%m','now')", one=True)['c']
    conformes  = query("SELECT COUNT(*) c FROM diagnosticos WHERE resultado='conforme'", one=True)['c']
    no_conf    = query("SELECT COUNT(*) c FROM diagnosticos WHERE resultado='no_conforme'", one=True)['c']
    alertas    = query("SELECT COUNT(*) c FROM alertas WHERE resuelta=0", one=True)['c']

    por_magnitud = rows_to_list(query("""
        SELECT magnitud, COUNT(*) total FROM diagnosticos GROUP BY magnitud ORDER BY total DESC
    """))

    recientes = rows_to_list(query("""
        SELECT d.n_certificado, d.resultado, d.fecha_fin, d.magnitud,
               e.codigo as equipo_codigo, e.descripcion as equipo_desc,
               u.nombre as tecnico
        FROM diagnosticos d
        JOIN equipos e ON e.id=d.equipo_id
        JOIN usuarios u ON u.id=d.tecnico_id
        ORDER BY d.creado DESC LIMIT 5
    """))

    vencimientos = rows_to_list(query("""
        SELECT e.codigo, e.descripcion, e.magnitud,
               MAX(d.prox_calibracion) as prox
        FROM equipos e
        LEFT JOIN diagnosticos d ON d.equipo_id=e.id
        WHERE e.activo=1
        GROUP BY e.id
        ORDER BY prox ASC LIMIT 6
    """))

    return jsonify({
        'diag_mes': diag_mes,
        'conformes': conformes,
        'no_conformes': no_conf,
        'alertas': alertas,
        'por_magnitud': por_magnitud,
        'recientes': recientes,
        'vencimientos': vencimientos,
    })
