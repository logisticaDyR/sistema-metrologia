"""
Tatronics — App Factory
"""
import os
from flask import Flask
from ..config import config


def create_app(config_name='default'):
    app = Flask(__name__, template_folder='templates', static_folder='static')
    app.config.from_object(config[config_name])

    # ── Ensure directories exist
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    os.makedirs(os.path.dirname(app.config['DATABASE_PATH']), exist_ok=True)

    # ── Initialize DB
    from calibpro_fixed.app.models.database import init_db
    init_db(app.config['DATABASE_PATH'])

    # ── Register Blueprints
    from .routes.auth      import auth_bp
    from .routes.dashboard import dashboard_bp
    from .routes.diagnostico import diagnostico_bp
    from .routes.equipos   import equipos_bp
    from .routes.clientes  import clientes_bp
    from .routes.reportes  import reportes_bp
    from .routes.api       import api_bp
    from .routes.home import home_bp
    from .routes.registro import registro_bp
    
    app.register_blueprint(home_bp)
    app.register_blueprint(registro_bp)

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(diagnostico_bp)
    app.register_blueprint(equipos_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    return app
