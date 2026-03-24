"""
Auth helper functions
"""
import hashlib
from functools import wraps
from flask import session, redirect, url_for, jsonify, request
from .database import query, execute, row_to_dict


def hash_password(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()


def get_user_by_email(email: str):
    row = query("SELECT * FROM usuarios WHERE email=? AND activo=1", (email,), one=True)
    return row_to_dict(row)


def get_user_by_id(uid: int):
    row = query("SELECT * FROM usuarios WHERE id=?", (uid,), one=True)
    return row_to_dict(row)


def login_user(email: str, password: str):
    user = get_user_by_email(email)
    if not user:
        return None, "Usuario no encontrado"
    if user['password'] != hash_password(password):
        return None, "Contraseña incorrecta"
    return user, None


def log_action(modulo, accion, objeto='', detalle=''):
    uid = session.get('user_id')
    ip  = request.remote_addr
    execute(
        "INSERT INTO audit_log(usuario_id,accion,modulo,objeto,detalle,ip) VALUES(?,?,?,?,?,?)",
        (uid, accion, modulo, objeto, detalle, ip)
    )


# ── Decorators

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_id' not in session:
            if request.is_json or request.path.startswith('/api/'):
                return jsonify({'error': 'No autenticado'}), 401
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated


def roles_required(*roles):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if session.get('user_rol') not in roles:
                if request.is_json or request.path.startswith('/api/'):
                    return jsonify({'error': 'Sin permiso'}), 403
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated
    return decorator
