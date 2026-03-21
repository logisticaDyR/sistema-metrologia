"""
Auth Blueprint — /login  /logout
"""
from flask import Blueprint, request, session, redirect, url_for, render_template, jsonify
from app.models.auth import login_user, log_action

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        data  = request.get_json() if request.is_json else request.form
        email = (data.get('email') or '').strip()
        pw    = (data.get('password') or '').strip()

        user, err = login_user(email, pw)
        if err:
            if request.is_json:
                return jsonify({'ok': False, 'error': err}), 401
            return render_template('login.html', error=err)

        session.permanent = True
        session['user_id']     = user['id']
        session['user_nombre'] = user['nombre']
        session['user_email']  = user['email']
        session['user_rol']    = user['rol']
        session['laboratorio'] = user['laboratorio']

        log_action('Auth', 'LOGIN', user['email'])

        if request.is_json:
            return jsonify({'ok': True, 'redirect': url_for('dashboard.index')})
        return redirect(url_for('dashboard.index'))

    return render_template('login.html')


@auth_bp.route('/logout')
def logout():
    log_action('Auth', 'LOGOUT', session.get('user_email', ''))
    session.clear()
    return redirect(url_for('auth.login'))
