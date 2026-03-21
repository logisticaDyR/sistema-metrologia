import hashlib
from flask import Blueprint, render_template, request, redirect, url_for
from app.models.database import execute, query

registro_bp = Blueprint('registro', __name__)

@registro_bp.route('/registro', methods=['GET', 'POST'])
def registro():
    error = None
    if request.method == 'POST':
        usuario = (request.form.get('usuario') or '').strip()
        email   = (request.form.get('email') or '').strip()
        pw      = (request.form.get('password') or '').strip()
        rol     = request.form.get('rol', 'tecnico').strip()
        lab     = request.form.get('laboratorio', 'Lab. Central').strip()

        if not usuario or not email or not pw:
            error = 'Todos los campos son obligatorios.'
        else:
            existing = query("SELECT id FROM usuarios WHERE email=?", (email,), one=True)
            if existing:
                error = 'Ya existe una cuenta con ese correo.'
            else:
                pw_hash = hashlib.sha256(pw.encode()).hexdigest()
                execute(
                    "INSERT INTO usuarios(nombre, email, password, rol, laboratorio) VALUES(?,?,?,?,?)",
                    (usuario, email, pw_hash, rol, lab)
                )
                return redirect(url_for('auth.login'))

    return render_template('registro.html', error=error)
