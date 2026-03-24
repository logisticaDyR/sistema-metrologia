"""
CalibPro — Sistema de Diagnóstico y Calibración
Entry point: python run.py
"""
from calibpro_fixed.app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)