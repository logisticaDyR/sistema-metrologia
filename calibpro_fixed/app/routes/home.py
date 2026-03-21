from flask import Blueprint, render_template, redirect, url_for

home_bp = Blueprint('home', __name__)

@home_bp.route('/')
def root():
    return redirect('/inicio')

@home_bp.route('/inicio')
def inicio():
    return render_template('home.html')