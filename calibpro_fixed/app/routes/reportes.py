"""
Reportes Blueprint — PDF generation (ReportLab) + Email
"""
import os, io, smtplib, base64
from email.mime.multipart import MIMEMultipart
from email.mime.text      import MIMEText
from email.mime.base      import MIMEBase
from email               import encoders
from datetime            import datetime

from flask import (Blueprint, request, jsonify, current_app,
                   send_file, session)
from calibpro_fixed.app.models.auth     import login_required, log_action
from calibpro_fixed.app.models.database import query, execute, rows_to_list, row_to_dict


reportes_bp = Blueprint('reportes', __name__)


# ─────────────────────────────────────────────
#  PDF GENERATION  (pure Python / ReportLab-free)
#  We generate an HTML string and return it, or
#  use reportlab if available, fallback to HTML.
# ─────────────────────────────────────────────

def _build_cert_html(diag, lecturas, fotos, upload_folder):
    """Build a self-contained HTML string for the certificate."""
    resultado_color = {
        'conforme':    '#16a34a',
        'no_conforme': '#dc2626',
        'observacion': '#d97706',
        'pendiente':   '#6b7280',
    }.get(diag.get('resultado', 'pendiente'), '#6b7280')

    resultado_texto = {
        'conforme':    'CONFORME ✅',
        'no_conforme': 'NO CONFORME ❌',
        'observacion': 'CONFORME CON OBSERVACIONES ⚠️',
        'pendiente':   'PENDIENTE',
    }.get(diag.get('resultado', 'pendiente'), 'PENDIENTE')

    # Build readings rows
    lecturas_html = ''
    for l in lecturas:
        color = '#16a34a'
        if abs(l.get('error_pct', 0)) > 0.4:
            color = '#d97706'
        if abs(l.get('error_pct', 0)) > 0.5:
            color = '#dc2626'
        lecturas_html += f"""
        <tr>
            <td>{l.get('valor_nominal','')}</td>
            <td>{l.get('porcentaje_rango','')}%</td>
            <td>{l.get('lectura_ebp','')}</td>
            <td>{l.get('lectura_patron','')}</td>
            <td style="color:{color}">{l.get('desviacion','')}</td>
            <td style="color:{color}">{l.get('error_pct','')}%</td>
            <td>±{l.get('incertidumbre','')}</td>
        </tr>"""

    # Build photos section
    fotos_html = ''
    if fotos:
        fotos_html = '<h3 style="color:#475569;font-size:12px;text-transform:uppercase;letter-spacing:1px;margin:20px 0 10px;border-bottom:1px solid #e2e8f0;padding-bottom:6px;">5. Registro Fotográfico del Diagnóstico</h3>'
        fotos_html += '<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:12px;">'
        for f in fotos:
            fpath = os.path.join(upload_folder, f['filename'])
            if os.path.exists(fpath):
                ext = f['filename'].rsplit('.', 1)[-1].lower()
                mime = 'image/png' if ext == 'png' else 'image/jpeg'
                with open(fpath, 'rb') as fp:
                    b64 = base64.b64encode(fp.read()).decode()
                fotos_html += f"""
                <div style="border:1px solid #e2e8f0;border-radius:8px;overflow:hidden;">
                    <img src="data:{mime};base64,{b64}" style="width:100%;height:160px;object-fit:cover;display:block;">
                    <div style="padding:6px 10px;background:#f8fafc;font-size:10px;color:#475569;font-weight:600;">📷 {f.get('label','Foto')}</div>
                </div>"""
        fotos_html += '</div>'

    html = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ font-family: Arial, sans-serif; margin: 0; padding: 30px; color: #1e293b; background: #fff; }}
  .header {{ display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:20px; padding-bottom:16px; border-bottom:2px solid #e2e8f0; }}
  .logo {{ font-size:22px; font-weight:800; color:#0a0e17; }}
  .logo span {{ color:#00d4aa; }}
  h2 {{ font-size:18px; margin:0 0 4px; }}
  .sub {{ font-size:11px; color:#64748b; }}
  .section-title {{ font-size:11px; text-transform:uppercase; letter-spacing:1px; color:#475569; margin:16px 0 8px; padding-bottom:5px; border-bottom:1px solid #e2e8f0; font-weight:700; }}
  .meta-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:10px 20px; margin-bottom:14px; }}
  .meta-item label {{ font-size:9px; text-transform:uppercase; color:#94a3b8; display:block; margin-bottom:3px; letter-spacing:0.5px; }}
  .meta-item span {{ font-size:12px; font-weight:600; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:14px; font-size:11px; }}
  th {{ background:#f8fafc; text-align:left; padding:7px 8px; font-size:9px; text-transform:uppercase; color:#94a3b8; }}
  td {{ padding:7px 8px; border-bottom:1px solid #f1f5f9; }}
  .result-box {{ padding:14px 16px; border-radius:8px; margin-top:12px; background:{resultado_color}18; border:1px solid {resultado_color}44; }}
  .result-val {{ font-size:20px; font-weight:800; color:{resultado_color}; }}
  .obs-box {{ font-size:10px; color:#64748b; margin-top:10px; padding:10px; background:#f8fafc; border-radius:6px; border-left:3px solid #cbd5e1; }}
  .sign-row {{ display:flex; gap:24px; margin-top:24px; padding-top:16px; border-top:1px solid #e2e8f0; }}
  .sign {{ flex:1; }}
  .sign-line {{ height:1px; background:#cbd5e1; margin-bottom:6px; margin-top:28px; }}
  .sign-name {{ font-size:10px; color:#64748b; }}
  .footer {{ margin-top:14px; text-align:center; font-size:9px; color:#94a3b8; border-top:1px solid #e2e8f0; padding-top:10px; }}
</style></head><body>

<div class="header">
  <div>
    <div class="logo">Tatronics</div>
    <div class="sub">Sistema de Metrología y Calibración</div>
    <div class="sub">Acreditado INACAL-DA-AC-0342 · ISO/IEC 17025:2017</div>
  </div>
  <div style="text-align:right;">
    <h2>CERTIFICADO DE CALIBRACIÓN</h2>
    <div class="sub">N° {diag.get('n_certificado','')}</div>
    <div class="sub">Fecha: {(diag.get('fecha_fin') or datetime.now().strftime('%Y-%m-%d %H:%M'))[:10]}</div>
  </div>
</div>

<div class="section-title">1. Identificación del Instrumento</div>
<div class="meta-grid">
  <div class="meta-item"><label>Descripción</label><span>{diag.get('equipo_desc','')}</span></div>
  <div class="meta-item"><label>Fabricante / Modelo</label><span>{diag.get('fabricante','')} {diag.get('modelo','')}</span></div>
  <div class="meta-item"><label>N° de serie</label><span>{diag.get('serie','')}</span></div>
  <div class="meta-item"><label>Código interno</label><span>{diag.get('equipo_codigo','')}</span></div>
  <div class="meta-item"><label>Rango de medición</label><span>{diag.get('rango','')}</span></div>
  <div class="meta-item"><label>Resolución</label><span>{diag.get('resolucion','')}</span></div>
  <div class="meta-item"><label>Cliente / Propietario</label><span>{diag.get('cliente_nombre','')}</span></div>
  <div class="meta-item"><label>Ubicación de uso</label><span>{diag.get('ubicacion','')}</span></div>
</div>

<div class="section-title">2. Condiciones Ambientales</div>
<div class="meta-grid">
  <div class="meta-item"><label>Temperatura inicio / fin</label><span>{diag.get('temp_inicio','')}°C / {diag.get('temp_fin','')}°C</span></div>
  <div class="meta-item"><label>Humedad relativa inicio / fin</label><span>{diag.get('humedad_inicio','')}% / {diag.get('humedad_fin','')}%</span></div>
  <div class="meta-item"><label>Presión atmosférica</label><span>{diag.get('presion_atm','')} hPa</span></div>
  <div class="meta-item"><label>Patrón utilizado</label><span>{diag.get('patron_codigo','')} — {diag.get('patron_desc','')}</span></div>
</div>

<div class="section-title">3. Resultados de la Calibración</div>
<table>
  <thead><tr><th>Nominal</th><th>% Rango</th><th>EBP</th><th>Patrón</th><th>Desviación</th><th>Error %FS</th><th>U (k=2)</th></tr></thead>
  <tbody>{lecturas_html}</tbody>
</table>

<div class="section-title">4. Resultado e Incertidumbre</div>
<div class="result-box">
  <div style="font-size:9px;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px;color:{resultado_color};">Resultado final</div>
  <div class="result-val">{resultado_texto}</div>
  <div style="font-size:11px;margin-top:6px;color:{resultado_color};">Dictamen: {diag.get('dictamen','')}</div>
</div>

<div class="obs-box"><b>Observaciones:</b> {diag.get('observaciones','')}</div>

{fotos_html}

<div class="sign-row">
  <div class="sign">
    <div class="sign-line"></div>
    <div class="sign-name"><b>{diag.get('tecnico_nombre','')}</b><br>Técnico Calibrador</div>
  </div>
  <div class="sign">
    <div class="sign-line"></div>
    <div class="sign-name"><b>Aprobado por Jefe de Laboratorio</b></div>
  </div>
</div>

<div class="footer">
  Verificar en: tatronicsperu.com/verificar/{diag.get('n_certificado','')}<br>
  Tatronics Perú · ISO/IEC 17025:2017 · INACAL-DA-AC-0342 · Lima, Perú
</div>
</body></html>"""
    return html


@reportes_bp.route('/api/diagnosticos/<int:did>/pdf')
@login_required
def get_pdf(did):
    """Return HTML certificate (browser prints/saves as PDF)."""
    row = query("""
        SELECT d.*, e.codigo equipo_codigo, e.descripcion equipo_desc,
               e.fabricante, e.modelo, e.serie, e.rango, e.resolucion, e.ubicacion,
               c.nombre as cliente_nombre,
               u.nombre as tecnico_nombre,
               p.codigo as patron_codigo, p.descripcion as patron_desc
        FROM diagnosticos d
        JOIN equipos e ON e.id=d.equipo_id
        LEFT JOIN clientes c ON c.id=e.cliente_id
        JOIN usuarios u ON u.id=d.tecnico_id
        LEFT JOIN patrones p ON p.id=d.patron_id
        WHERE d.id=?
    """, (did,), one=True)

    if not row:
        return 'Diagnóstico no encontrado', 404

    diag     = dict(row)
    lecturas = rows_to_list(query(
        "SELECT * FROM lecturas WHERE diagnostico_id=? ORDER BY ciclo,punto", (did,)))
    fotos    = rows_to_list(query(
        "SELECT * FROM fotos WHERE diagnostico_id=?", (did,)))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    html = _build_cert_html(diag, lecturas, fotos, upload_folder)

    buf = io.BytesIO(html.encode('utf-8'))
    buf.seek(0)
    log_action('Reportes', 'PDF', diag['n_certificado'])
    return send_file(buf, mimetype='text/html',
                     download_name=f"{diag['n_certificado']}.html",
                     as_attachment=False)

from reportlab.lib.pagesizes import letter
from reportlab.lib             import colors
from reportlab.lib.styles      import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units       import cm
from reportlab.platypus        import (SimpleDocTemplate, Paragraph, Spacer,
                                       Table, TableStyle, HRFlowable)
from reportlab.lib.enums       import TA_LEFT, TA_CENTER, TA_RIGHT


# ── Color palette matching the HTML certificate ──────────────────────────────
C_DARK      = colors.HexColor('#1e293b')
C_MUTED     = colors.HexColor('#64748b')
C_LIGHT     = colors.HexColor('#94a3b8')
C_BORDER    = colors.HexColor('#e2e8f0')
C_BG        = colors.HexColor('#f8fafc')
C_ACCENT    = colors.HexColor('#00d4aa')
C_CONFORM   = colors.HexColor('#16a34a')
C_NOCONF    = colors.HexColor('#dc2626')
C_OBS       = colors.HexColor('#d97706')
C_PENDING   = colors.HexColor('#6b7280')

RESULTADO_COLOR = {
    'conforme':    C_CONFORM,
    'no_conforme': C_NOCONF,
    'observacion': C_OBS,
    'pendiente':   C_PENDING,
}
RESULTADO_HEX = {
    'conforme':    '#16a34a',
    'no_conforme': '#dc2626',
    'observacion': '#d97706',
    'pendiente':   '#6b7280',
}
RESULTADO_BG = {
    'conforme':    colors.HexColor('#dcfce7'),
    'no_conforme': colors.HexColor('#fee2e2'),
    'observacion': colors.HexColor('#fef3c7'),
    'pendiente':   colors.HexColor('#f3f4f6'),
}
RESULTADO_TEXTO = {
    'conforme':    'CONFORME',
    'no_conforme': 'NO CONFORME',
    'observacion': 'CONFORME CON OBSERVACIONES',
    'pendiente':   'PENDIENTE',
}


def generate_cert_pdf(buf, diag, lecturas, fotos, upload_folder):
    """Generate a fully-formatted certificate PDF into a BytesIO buffer."""
    doc = SimpleDocTemplate(
        buf, pagesize=letter,
        leftMargin=1.8*cm, rightMargin=1.8*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    styles = getSampleStyleSheet()

    # ── Custom styles ─────────────────────────────────────────────────────────
    def S(name, **kw):
        return ParagraphStyle(name, parent=styles['Normal'], **kw)

    s_logo    = S('logo',   fontSize=18, fontName='Helvetica-Bold', textColor=C_DARK, leading=22)
    s_sub     = S('sub',    fontSize=8,  textColor=C_MUTED, leading=11)
    s_title   = S('title',  fontSize=14, fontName='Helvetica-Bold', textColor=C_DARK,
                  alignment=TA_RIGHT, leading=18)
    s_cert_no = S('certno', fontSize=9,  textColor=C_MUTED, alignment=TA_RIGHT)
    s_sec     = S('sec',    fontSize=8,  fontName='Helvetica-Bold', textColor=C_MUTED,
                  spaceAfter=4, spaceBefore=10, textTransform='uppercase')
    s_lbl     = S('lbl',    fontSize=7,  textColor=C_LIGHT, leading=9)
    s_val     = S('val',    fontSize=10, fontName='Helvetica-Bold', textColor=C_DARK, leading=13)
    s_th      = S('th',     fontSize=7,  fontName='Helvetica-Bold', textColor=C_LIGHT,
                  alignment=TA_CENTER, textTransform='uppercase')
    s_td      = S('td',     fontSize=8,  textColor=C_DARK, alignment=TA_CENTER, leading=11)
    s_obs     = S('obs',    fontSize=8,  textColor=C_MUTED, leading=11)
    s_sign    = S('sign',   fontSize=8,  textColor=C_MUTED, alignment=TA_CENTER, leading=11)
    s_footer  = S('footer', fontSize=7,  textColor=C_LIGHT, alignment=TA_CENTER, leading=10)
    s_res_lbl = S('reslbl', fontSize=7,  textColor=C_MUTED, leading=10, textTransform='uppercase')

    resultado  = diag.get('resultado', 'pendiente')
    res_color  = RESULTADO_COLOR.get(resultado, C_PENDING)
    res_hex    = RESULTADO_HEX.get(resultado, '#6b7280')
    res_bg     = RESULTADO_BG.get(resultado, colors.HexColor('#f3f4f6'))
    res_texto  = RESULTADO_TEXTO.get(resultado, 'PENDIENTE')
    fecha      = (diag.get('fecha_fin') or datetime.now().strftime('%Y-%m-%d %H:%M'))[:10]

    story = []

    # ── Header ────────────────────────────────────────────────────────────────
    header_data = [[
        [Paragraph('Tatronics', s_logo),
         Paragraph('Sistema de Metrología y Calibración', s_sub),
         Paragraph('Acreditado INACAL-DA-AC-0342 · ISO/IEC 17025:2017', s_sub)],
        [Paragraph('CERTIFICADO DE CALIBRACIÓN', s_title),
         Paragraph(f"N° {diag.get('n_certificado','')}", s_cert_no),
         Paragraph(f"Fecha: {fecha}", s_cert_no)],
    ]]
    ht = Table(header_data, colWidths=['55%', '45%'])
    ht.setStyle(TableStyle([
        ('VALIGN',      (0,0), (-1,-1), 'TOP'),
        ('LINEBELOW',   (0,0), (-1,-1), 1, C_BORDER),
        ('BOTTOMPADDING',(0,0),(-1,-1), 10),
    ]))
    story.append(ht)
    story.append(Spacer(1, 8))

    # ── Section helper ────────────────────────────────────────────────────────
    def section(title):
        story.append(Paragraph(title, s_sec))
        story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=6))

    def meta_grid(pairs):
        """Render a list of (label, value) pairs in a 2-column grid."""
        rows = []
        for i in range(0, len(pairs), 2):
            row = []
            for label, value in pairs[i:i+2]:
                row.append([Paragraph(label, s_lbl), Paragraph(str(value or '—'), s_val)])
            if len(row) == 1:
                row.append('')
            rows.append(row)
        t = Table(rows, colWidths=['50%', '50%'])
        t.setStyle(TableStyle([
            ('VALIGN',       (0,0), (-1,-1), 'TOP'),
            ('TOPPADDING',   (0,0), (-1,-1), 3),
            ('BOTTOMPADDING',(0,0), (-1,-1), 5),
        ]))
        story.append(t)

    # ── 1. Instrument ID ──────────────────────────────────────────────────────
    section('1. Identificación del Instrumento')
    meta_grid([
        ('Descripción',        diag.get('equipo_desc','')),
        ('Fabricante / Modelo', f"{diag.get('fabricante','')} {diag.get('modelo','')}".strip()),
        ('N° de serie',         diag.get('serie','')),
        ('Código interno',      diag.get('equipo_codigo','')),
        ('Rango de medición',   diag.get('rango','')),
        ('Resolución',          diag.get('resolucion','')),
        ('Cliente / Propietario', diag.get('cliente_nombre','')),
        ('Ubicación de uso',    diag.get('ubicacion','')),
    ])

    # ── 2. Environmental conditions ───────────────────────────────────────────
    section('2. Condiciones Ambientales')
    meta_grid([
        ('Temperatura inicio / fin',
         f"{diag.get('temp_inicio','')}°C / {diag.get('temp_fin','')}°C"),
        ('Humedad relativa inicio / fin',
         f"{diag.get('humedad_inicio','')}% / {diag.get('humedad_fin','')}%"),
        ('Presión atmosférica',  f"{diag.get('presion_atm','')} hPa"),
        ('Patrón utilizado',
         f"{diag.get('patron_codigo','')}" +
         (f" — {diag.get('patron_desc','')}" if diag.get('patron_desc') else '')),
    ])

    # ── 3. Readings table ─────────────────────────────────────────────────────
    section('3. Resultados de la Calibración')
    headers = ['Nominal', '% Rango', 'EBP', 'Patrón', 'Desviación', 'Error %FS', 'U (k=2)']
    t_data  = [[Paragraph(h, s_th) for h in headers]]
    for l in lecturas:
        ep = abs(l.get('error_pct', 0) or 0)
        cell_color = C_CONFORM if ep <= 0.4 else (C_OBS if ep <= 0.5 else C_NOCONF)
        row = [
            Paragraph(str(l.get('valor_nominal', '')),   s_td),
            Paragraph(f"{l.get('porcentaje_rango','')}%", s_td),
            Paragraph(str(l.get('lectura_ebp',   '')),   s_td),
            Paragraph(str(l.get('lectura_patron','')),   s_td),
            Paragraph(str(l.get('desviacion',    '')),
                      ParagraphStyle('tdc', parent=s_td, textColor=cell_color)),
            Paragraph(f"{l.get('error_pct','')}%",
                      ParagraphStyle('tde', parent=s_td, textColor=cell_color)),
            Paragraph(f"±{l.get('incertidumbre','')}",  s_td),
        ]
        t_data.append(row)
    col_w = ['13%','11%','13%','13%','15%','15%','13%']  # roughly 100% together, adjust to page
    readings_t = Table(t_data, colWidths=col_w, repeatRows=1)
    readings_t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0), (-1,0), C_BG),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white, colors.HexColor('#f8fafc')]),
        ('GRID',         (0,0), (-1,-1), 0.3, C_BORDER),
        ('TOPPADDING',   (0,0), (-1,-1), 4),
        ('BOTTOMPADDING',(0,0), (-1,-1), 4),
    ]))
    story.append(readings_t)
    story.append(Spacer(1, 8))

    # ── 4. Result box ─────────────────────────────────────────────────────────
    section('4. Resultado e Incertidumbre')
    res_inner = [
        [Paragraph('Resultado final', s_res_lbl)],
        [Paragraph(f'<font color="{res_hex}" size="15"><b>{res_texto}</b></font>',
                   ParagraphStyle('rv', parent=styles['Normal'], leading=20))],
        [Paragraph(f'Dictamen: {diag.get("dictamen","")}',
                   ParagraphStyle('dict', parent=s_obs, textColor=res_color))],
    ]
    res_t = Table(res_inner, colWidths=['100%'])
    res_t.setStyle(TableStyle([
        ('BACKGROUND',    (0,0), (-1,-1), res_bg),
        ('BOX',           (0,0), (-1,-1), 0.5, res_color),
        ('TOPPADDING',    (0,0), (-1,-1), 8),
        ('BOTTOMPADDING', (0,0), (-1,-1), 8),
        ('LEFTPADDING',   (0,0), (-1,-1), 10),
    ]))
    story.append(res_t)
    story.append(Spacer(1, 6))

    # Observations
    obs_t = Table([[Paragraph(
        f"<b>Observaciones:</b> {diag.get('observaciones','')}", s_obs)]],
        colWidths=['100%'])
    obs_t.setStyle(TableStyle([
        ('BACKGROUND',   (0,0),(-1,-1), C_BG),
        ('LINERIGHT',    (0,0),(0,-1),  2, C_BORDER),
        ('TOPPADDING',   (0,0),(-1,-1), 6),
        ('BOTTOMPADDING',(0,0),(-1,-1), 6),
        ('LEFTPADDING',  (0,0),(-1,-1), 8),
    ]))
    story.append(obs_t)

    # ── 5. Photos ─────────────────────────────────────────────────────────────
    if fotos:
        from reportlab.platypus import Image as RLImage
        valid_photos = []
        for f in fotos:
            fpath = os.path.join(upload_folder, f['filename'])
            if os.path.exists(fpath):
                valid_photos.append((fpath, f.get('label', 'Foto')))
        if valid_photos:
            section('5. Registro Fotográfico del Diagnóstico')
            photo_rows = []
            for i in range(0, len(valid_photos), 2):
                row = []
                for fpath, label in valid_photos[i:i+2]:
                    try:
                        img = RLImage(fpath, width=7*cm, height=5*cm)
                        img.hAlign = 'CENTER'
                        row.append([img, Paragraph(f'📷 {label}', s_sign)])
                    except Exception:
                        row.append(Paragraph(label, s_sign))
                if len(row) == 1:
                    row.append('')
                photo_rows.append(row)
            pt = Table(photo_rows, colWidths=['50%', '50%'])
            pt.setStyle(TableStyle([
                ('BOX',          (0,0),(-1,-1), 0.5, C_BORDER),
                ('INNERGRID',    (0,0),(-1,-1), 0.5, C_BORDER),
                ('TOPPADDING',   (0,0),(-1,-1), 6),
                ('BOTTOMPADDING',(0,0),(-1,-1), 6),
                ('ALIGN',        (0,0),(-1,-1), 'CENTER'),
            ]))
            story.append(pt)

    # ── Signature row ─────────────────────────────────────────────────────────
    story.append(Spacer(1, 16))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER))
    story.append(Spacer(1, 6))
    sign_data = [[
        Paragraph(f"<b>{diag.get('tecnico_nombre','')}</b><br/>Técnico Calibrador", s_sign),
        Paragraph('<b>Aprobado por Jefe de Laboratorio</b>', s_sign),
    ]]
    st = Table(sign_data, colWidths=['50%', '50%'])
    st.setStyle(TableStyle([
        ('LINEABOVE',    (0,0),(-1,-1), 0.5, C_BORDER),
        ('TOPPADDING',   (0,0),(-1,-1), 6),
        ('ALIGN',        (0,0),(-1,-1), 'CENTER'),
    ]))
    story.append(st)

    # ── Footer ────────────────────────────────────────────────────────────────
    story.append(Spacer(1, 10))
    story.append(HRFlowable(width='100%', thickness=0.5, color=C_BORDER, spaceAfter=4))
    story.append(Paragraph(
        f"Verificar en: tatronicsperu.com/verificar/{diag.get('n_certificado','')}<br/>"
        "Tatronics Perú · ISO/IEC 17025:2017 · INACAL-DA-AC-0342 · Lima, Perú",
        s_footer))

    doc.build(story)

@reportes_bp.route('/api/diagnosticos/<int:did>/email', methods=['POST'])
@login_required
def send_email(did):
    """Send certificate by email."""
    data = request.get_json() or {}
    to      = data.get('to', '')
    cc      = data.get('cc', '')
    subject = data.get('subject', f'Certificado de Calibración')
    body    = data.get('body', '')

    if not to:
        return jsonify({'ok': False, 'error': 'Destinatario requerido'}), 400

    row = query("""
        SELECT d.*, e.codigo equipo_codigo, e.descripcion equipo_desc,
               e.fabricante, e.modelo, e.serie, e.rango, e.resolucion, e.ubicacion,
               c.nombre as cliente_nombre, c.email as cliente_email,
               u.nombre as tecnico_nombre,
               p.codigo as patron_codigo, p.descripcion as patron_desc
        FROM diagnosticos d
        JOIN equipos e ON e.id=d.equipo_id
        LEFT JOIN clientes c ON c.id=e.cliente_id
        JOIN usuarios u ON u.id=d.tecnico_id
        LEFT JOIN patrones p ON p.id=d.patron_id
        WHERE d.id=?
    """, (did,), one=True)

    if not row:
        return jsonify({'ok': False, 'error': 'Diagnóstico no encontrado'}), 404

    diag     = dict(row)
    lecturas = rows_to_list(query(
        "SELECT * FROM lecturas WHERE diagnostico_id=? ORDER BY ciclo,punto", (did,)))
    fotos    = rows_to_list(query(
        "SELECT * FROM fotos WHERE diagnostico_id=?", (did,)))

    upload_folder = current_app.config['UPLOAD_FOLDER']
    cfg = current_app.config
    if not cfg.get('MAIL_USERNAME'):
        # Simulate success for development
        execute("UPDATE diagnosticos SET enviado_email=1 WHERE id=?", (did,))
        log_action('Email', 'ENVIADO (simulado)', diag['n_certificado'], f'→ {to}')
        return jsonify({'ok': True, 'mode': 'simulated',
                        'message': f'Simulación OK. Configure MAIL_USERNAME para envío real.'})

    try:
        msg = MIMEMultipart('mixed')
        msg['From']    = cfg['MAIL_DEFAULT_SENDER']
        msg['To']      = to
        if cc: msg['Cc'] = cc
        msg['Subject'] = subject

        # HTML body
        html_body = f"<html><body><p>{body.replace(chr(10),'<br>')}</p></body></html>"
        msg.attach(MIMEText(html_body, 'html', 'utf-8'))

        # Generar PDF con ReportLab y adjuntarlo
        pdf_buf = io.BytesIO()
        generate_cert_pdf(pdf_buf, diag, lecturas, fotos, upload_folder)
        pdf_buf.seek(0)
        att = MIMEBase('application', 'pdf')
        att.set_payload(pdf_buf.read())
        encoders.encode_base64(att)
        att.add_header(
            'Content-Disposition',
            'attachment',
            filename=f"{diag['n_certificado']}.pdf"
        )
        msg.attach(att)

        with smtplib.SMTP(cfg['MAIL_SERVER'], cfg['MAIL_PORT']) as server:
            server.ehlo()
            if cfg['MAIL_USE_TLS']:
                server.starttls()
            server.login(cfg['MAIL_USERNAME'], cfg['MAIL_PASSWORD'])
            recipients = [to] + ([cc] if cc else [])
            server.sendmail(cfg['MAIL_DEFAULT_SENDER'], recipients, msg.as_string())

        execute("UPDATE diagnosticos SET enviado_email=1 WHERE id=?", (did,))
        log_action('Email', 'ENVIADO', diag['n_certificado'], f'→ {to}')
        return jsonify({'ok': True, 'message': f'Correo enviado a {to}'})

    except Exception as e:
        return jsonify({'ok': False, 'error': str(e)}), 500


@reportes_bp.route('/api/alertas')
@login_required
def list_alertas():
    rows = rows_to_list(query(
        "SELECT * FROM alertas ORDER BY resuelta ASC, creado DESC"))
    return jsonify(rows)


@reportes_bp.route('/api/alertas/<int:aid>/resolver', methods=['POST'])
@login_required
def resolver_alerta(aid):
    execute("UPDATE alertas SET resuelta=1 WHERE id=?", (aid,))
    return jsonify({'ok': True})


@reportes_bp.route('/api/alertas/<int:aid>', methods=['DELETE'])
@login_required
def delete_alerta(aid):
    execute("DELETE FROM alertas WHERE id=?", (aid,))
    log_action('Alertas', 'ELIMINAR', str(aid))
    return jsonify({'ok': True})


@reportes_bp.route('/api/audit')
@login_required
def audit_log():
    rows = rows_to_list(query("""
        SELECT a.*, u.nombre as usuario_nombre
        FROM audit_log a LEFT JOIN usuarios u ON u.id=a.usuario_id
        ORDER BY a.ts DESC LIMIT 50
    """))
    return jsonify(rows)


@reportes_bp.route('/api/estadisticas')
@login_required
def estadisticas():
    por_resultado = rows_to_list(query(
        "SELECT resultado, COUNT(*) total FROM diagnosticos GROUP BY resultado"))
    por_mes = rows_to_list(query("""
        SELECT strftime('%Y-%m',creado) mes, COUNT(*) total
        FROM diagnosticos GROUP BY mes ORDER BY mes DESC LIMIT 12
    """))
    por_magnitud = rows_to_list(query(
        "SELECT magnitud, COUNT(*) total FROM diagnosticos GROUP BY magnitud"))
    return jsonify({
        'por_resultado': por_resultado,
        'por_mes': por_mes,
        'por_magnitud': por_magnitud,
    })
