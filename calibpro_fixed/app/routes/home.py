from flask import Blueprint, render_template, redirect, url_for

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def root():
    return redirect('/inicio')

@home_bp.route('/inicio')
def inicio():
    return render_template('paginas/inicio.html')

@home_bp.route('/nosotros')
def nosotros():
    return render_template('paginas/nosotros.html')

@home_bp.route('/servicios')
def servicios():
    return render_template('paginas/servicios.html')

@home_bp.route('/clientes')
def clientes():
    return render_template('paginas/clientes.html')

@home_bp.route('/contacto')
def contacto():
    return render_template('paginas/contacto.html')
