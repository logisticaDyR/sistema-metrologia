# CalibPro — Sistema de Diagnóstico y Calibración
## ISO/IEC 17025 · Metrología Industrial

---

## 📁 Estructura del Proyecto

```
calibpro/
├── run.py                    ← Punto de entrada
├── config.py                 ← Configuración (DB, email, uploads)
├── requirements.txt
├── database/
│   └── calibpro.db           ← SQLite (auto-generada)
├── uploads/
│   └── photos/               ← Fotos de diagnósticos
└── app/
    ├── __init__.py           ← App factory
    ├── models/
    │   ├── database.py       ← Schema SQL, CRUD helpers, seed data
    │   └── auth.py           ← Login, sesiones, decoradores
    ├── routes/
    │   ├── auth.py           ← /login  /logout
    │   ├── dashboard.py      ← /  /api/dashboard/stats
    │   ├── diagnostico.py    ← /api/diagnosticos  (CRUD + fotos + lecturas)
    │   ├── equipos.py        ← /api/equipos
    │   ├── clientes.py       ← /api/clientes
    │   ├── reportes.py       ← /api/.../pdf  /api/.../email  /api/alertas
    │   └── api.py            ← /api/patrones  /api/usuarios  /api/search
    ├── templates/
    │   ├── login.html
    │   └── app.html
    └── static/
        ├── css/main.css
        └── js/main.js
```

---

## 🚀 Instalación y Arranque

```bash
cd calibpro
pip install Flask
python run.py
```

Accede en: **http://localhost:5000**

---

## 👤 Cuentas de Prueba

| Email | Contraseña | Rol |
|-------|-----------|-----|
| admin@calibpro.com | admin123 | Administrador |
| jefe@calibpro.com | jefe123 | Jefe de Lab. |
| p.torres@calibpro.com | tecnico123 | Técnico |

---

## 📧 Configuración de Correo (Opcional)

En `config.py` o variables de entorno:
```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=tu@gmail.com
MAIL_PASSWORD=tu_app_password
```
Sin configurar: el envío se simula (se graba en BD sin enviar realmente).

---

## 🗄️ Base de Datos — Tablas

| Tabla | Descripción |
|-------|-------------|
| `usuarios` | Personal del laboratorio |
| `clientes` | Clientes y propietarios de equipos |
| `equipos` | Inventario de instrumentos a calibrar |
| `patrones` | Patrones de referencia con trazabilidad |
| `diagnosticos` | Diagnósticos de calibración (cabecera) |
| `lecturas` | Puntos de medición por diagnóstico |
| `fotos` | Imágenes capturadas por diagnóstico |
| `alertas` | Alertas activas del sistema |
| `audit_log` | Registro de auditoría de acciones |

---

## 🔌 API Endpoints Principales

```
POST   /login
GET    /logout

GET    /api/dashboard/stats
GET    /api/diagnosticos          ?q=&magnitud=&page=
POST   /api/diagnosticos
GET    /api/diagnosticos/<id>
PUT    /api/diagnosticos/<id>
POST   /api/diagnosticos/<id>/lecturas
POST   /api/diagnosticos/<id>/fotos    (multipart o base64 JSON)
GET    /api/diagnosticos/<id>/pdf      (HTML del certificado)
POST   /api/diagnosticos/<id>/email
DELETE /api/fotos/<id>

GET    /api/equipos               ?q=&magnitud=
POST   /api/equipos
PUT    /api/equipos/<id>
DELETE /api/equipos/<id>

GET/POST /api/clientes
GET/POST /api/patrones
GET      /api/usuarios
GET      /api/search              ?q=
GET      /api/alertas
POST     /api/alertas/<id>/resolver
GET      /api/estadisticas
GET      /api/audit
GET      /fotos/<filename>
```
