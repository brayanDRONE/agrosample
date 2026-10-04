from datetime import datetime
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import KeepInFrame, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from types import SimpleNamespace


NAVY = colors.HexColor('#15324B')
BLUE = colors.HexColor('#DCEBF6')
GREEN = colors.HexColor('#DDF2E4')
TEAL = colors.HexColor('#D9F0EC')
VIOLET = colors.HexColor('#ECE8F7')
PALE = colors.HexColor('#F5F8FA')
GRID = colors.HexColor('#C8D5DC')
TEXT = colors.HexColor('#233746')
MUTED = colors.HexColor('#657987')
GOOD = colors.HexColor('#18864B')
BAD = colors.HexColor('#B42318')
UNKNOWN = colors.HexColor('#B96C00')
WHITE = colors.white


def _p(value, style, color=None):
    text = escape(str(value if value not in (None, '') else '-')).replace('\n', '<br/>')
    if color:
        text = f'<font color="{color.hexval()}">{text}</font>'
    return Paragraph(text, style)


def _status(value):
    if isinstance(value, str) and value.upper() == 'NO INGRESADO':
        return 'NO INGRESADO', MUTED
    if value is True:
        return 'SI', GOOD
    if value is False:
        return 'NO', BAD
    return 'NO VERIFICADO', UNKNOWN


def _panel(title, rows, width, styles, accent=BLUE, status_rows=False):
    title_style = styles['panel_title']
    label_style = styles['label']
    value_style = styles['value']
    data = [[Paragraph(escape(title), title_style), '']]
    commands = [
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), accent),
        ('BOX', (0, 0), (-1, -1), 0.7, GRID),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]
    for label, value in rows:
        if status_rows:
            label_text, label_color = _status(value)
            data.append([_p(label, label_style), _p(f'●  {label_text}', value_style, label_color)])
        else:
            data.append([_p(label, label_style), _p(value, value_style)])
    table = Table(data, colWidths=[width * 0.58, width * 0.42], hAlign='LEFT')
    table.setStyle(TableStyle(commands))
    return table


def _campaign_panel(results, width, styles):
    rows = [['CÓDIGO', 'CAMPAÑA', 'PAÍS']]
    csgs = results.get('csgs') or ([results.get('csg')] if results.get('csg') else [])
    subjects = [(subject, 'CSG') for subject in csgs]
    csps = results.get('csps') or ([results.get('csp')] if results.get('csp', {}).get('code') else [])
    subjects.extend((subject, 'CSP') for subject in csps)
    for subject, code_type in subjects:
        code = subject.get('code') or code_type
        found = subject.get('mosca_campaign_found')
        current = subject.get('mosca_campaign_current')
        campaigns = subject.get('mosca_campaigns') or []
        if campaigns:
            rows.extend([[code, item.get('campaign') or '-', item.get('country') or '-'] for item in campaigns[:5]])
            if len(campaigns) > 5:
                rows.append([code, f'+{len(campaigns) - 5} campañas', 'Ver listado'])
        elif found is False:
            rows.append([code, 'No figura en listado', '-'])
        elif found is True and current is False:
            rows.append([code, 'Figura sin campaña vigente', '-'])
        elif found is None:
            rows.append([code, 'No verificado', '-'])
        else:
            rows.append([code, 'Sin campaña vigente', '-'])

    title_style = styles['panel_title']
    small = styles['small']
    table_data = [[Paragraph('CAMPAÑAS Y PAÍSES', title_style), '', '']]
    table_data.append([_p(cell, styles['table_header']) for cell in rows[0]])
    table_data.extend([[_p(cell, small) for cell in row] for row in rows[1:]])
    code_width = min(0.72 * inch, width * 0.18)
    remaining_width = width - code_width
    table = Table(table_data, colWidths=[code_width, remaining_width * 0.52, remaining_width * 0.48])
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), VIOLET),
        ('BACKGROUND', (0, 1), (-1, 1), PALE),
        ('BOX', (0, 0), (-1, -1), 0.7, GRID),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return table


def _csp_panel(csps, width, styles):
    csps = csps or []
    header = [
        _p('CSP', styles['table_header']),
        _p('INSCRITO CHINA', styles['table_header']),
        _p('APROBADO SAG', styles['table_header']),
        _p('CAMPAÑA', styles['table_header']),
    ]
    rows = [header]
    if csps:
        for csp in csps:
            rows.append([
                _p(csp.get('code') or '-', styles['value']),
                _p(_status(csp.get('china_registered'))[0], styles['small']),
                _p(_status(csp.get('china_approved'))[0], styles['small']),
                _p(_status(csp.get('mosca_campaign_current'))[0], styles['small']),
            ])
    else:
        rows.append([_p('No ingresado', styles['small']), _p('-', styles['small']), _p('-', styles['small']), _p('-', styles['small'])])
    table = Table(
        [[Paragraph('PACKING / CSP', styles['panel_title']), '', '', ''], *rows],
        colWidths=[width * 0.21, width * 0.28, width * 0.25, width * 0.26],
        repeatRows=2,
    )
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), TEAL),
        ('BACKGROUND', (0, 1), (-1, 1), PALE),
        ('BOX', (0, 0), (-1, -1), 0.7, GRID),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]))
    return table


def _descolgados_panel(report, csgs, width, styles):
    data = [['CSG', 'VARIEDAD', 'PLAGA', 'PAÍS A DESCOLGAR']]
    for subject in csgs:
        code = subject.get('code') or '-'
        detections = subject.get('descolgados') or []
        if detections:
            data.extend([
                [
                    item.get('csg') or code,
                    item.get('variety') or '-',
                    item.get('pest') or '-',
                    item.get('target_country') or '-',
                ]
                for item in detections[:4]
            ])
            if len(detections) > 4:
                data.append([code, f'+{len(detections) - 4} detecciones', '-', '-'])
        else:
            result = 'Sin descolgados cereza-China' if subject.get('descolgado_china') is False else 'No verificado'
            data.append([code, result, '-', '-'])
    if not csgs:
        data.append([report.csg or '-', 'No ingresado', '-', '-'])

    table_data = [[Paragraph('DESCOLGADOS PARA CEREZA CHINA', styles['panel_title']), '', '', '']]
    table_data.extend([[_p(cell, styles['table_header']) for cell in data[0]]])
    table_data.extend([[_p(cell, styles['small']) for cell in row] for row in data[1:]])
    code_width = min(0.72 * inch, width * 0.16)
    remaining_width = width - code_width
    table = Table(
        table_data,
        colWidths=[code_width, remaining_width * 0.30, remaining_width * 0.34, remaining_width * 0.36],
    )
    table.setStyle(TableStyle([
        ('SPAN', (0, 0), (-1, 0)),
        ('BACKGROUND', (0, 0), (-1, 0), VIOLET),
        ('BACKGROUND', (0, 1), (-1, 1), PALE),
        ('BOX', (0, 0), (-1, -1), 0.7, GRID),
        ('INNERGRID', (0, 0), (-1, -1), 0.35, GRID),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    return table


def _csg_overview_panel(csg, width, styles):
    code = csg.get('code') or '-'
    rows = [
        ('Productor', csg.get('producer_name') or 'No verificado'),
        ('Predio', csg.get('establishment_name') or 'No verificado'),
        ('Estado SRA', 'ACTIVO' if csg.get('active') is True else ('INACTIVO' if csg.get('active') is False else 'NO VERIFICADO')),
        ('Inscrito China', _status(csg.get('china_registered'))[0]),
        ('ChinaPort cereza', _status(csg.get('china_cherry_approved'))[0]),
        ('En listado mosca', _status(csg.get('mosca_campaign_found'))[0]),
        ('Campaña vigente', _status(csg.get('mosca_campaign_current'))[0]),
        ('Descolgado China', _status(csg.get('descolgado_china'))[0]),
        ('Producto ChinaPort', csg.get('chinaport_product_name') or 'No verificado'),
        ('Nombre científico', csg.get('chinaport_scientific_name') or 'No verificado'),
        ('Variedades', ', '.join(csg.get('varieties') or []) or 'No verificadas'),
    ]
    return _panel(f'HUERTO / CSG {code}', rows, width, styles, BLUE)


def _build_validation_pdf_page(report, results, sources):
    buffer = BytesIO()
    page_width, page_height = letter
    margins = 0.34 * inch
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=margins,
        leftMargin=margins,
        topMargin=margins,
        bottomMargin=margins,
        title='Informe de Verificación CSG/CSP · China',
        author='AgroSample',
    )
    usable_width = page_width - (2 * margins)
    usable_height = page_height - (2 * margins)
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name='report_title', parent=styles['Title'], fontName='Helvetica-Bold',
        fontSize=20, leading=24, alignment=TA_LEFT, textColor=WHITE, spaceAfter=0,
    ))
    styles.add(ParagraphStyle(
        name='report_meta', parent=styles['BodyText'], fontSize=9, leading=11,
        alignment=TA_RIGHT, textColor=WHITE,
    ))
    styles.add(ParagraphStyle(
        name='panel_title', parent=styles['BodyText'], fontName='Helvetica-Bold',
        fontSize=10.5, leading=12.5, textColor=NAVY,
    ))
    styles.add(ParagraphStyle(
        name='label', parent=styles['BodyText'], fontSize=9.5, leading=11.5, textColor=MUTED,
    ))
    styles.add(ParagraphStyle(
        name='value', parent=styles['BodyText'], fontName='Helvetica-Bold',
        fontSize=10.3, leading=12.5, textColor=TEXT,
    ))
    styles.add(ParagraphStyle(
        name='small', parent=styles['BodyText'], fontSize=8.5, leading=10.5, textColor=TEXT,
    ))
    styles.add(ParagraphStyle(
        name='table_header', parent=styles['BodyText'], fontName='Helvetica-Bold',
        fontSize=7.8, leading=9.5, textColor=NAVY,
    ))
    csgs = results.get('csgs') or ([results.get('csg')] if results.get('csg') else [])
    csg = csgs[0] if csgs else {}
    csps = results.get('csps') or ([results.get('csp')] if results.get('csp', {}).get('code') else [])
    csp = csps[0] if csps else {}
    csg_code = csg.get('code') or report.csg or ''
    csp_code = csp.get('code') or report.csp or ''
    heading = 'INFORME DE VERIFICACIÓN CSG' if csg_code else 'INFORME DE VERIFICACIÓN CSP'

    page_indicator = getattr(report, 'page_indicator', '')
    meta_text = f'CHINA<br/>Fecha: {datetime.now():%d-%m-%Y}'
    if page_indicator:
        meta_text += f'<br/>{escape(page_indicator)}'
    header = Table([[
        Paragraph(escape(heading), styles['report_title']),
        Paragraph(meta_text, styles['report_meta']),
    ]], colWidths=[usable_width * 0.74, usable_width * 0.26])
    header.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), NAVY),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
    ]))

    if len(csgs) > 1:
        card_width = (usable_width - 10) / 2
        main_panels = Table(
            [[_csg_overview_panel(subject, card_width, styles) for subject in csgs]],
            colWidths=[card_width, card_width],
            hAlign='LEFT',
        )
        main_panels.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 5),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))
    else:
        verification_rows = [
            ('Estado SRA', csg.get('active')),
            ('CSG inscrito para China', csg.get('china_registered')),
            ('ChinaPort: habilitado para cereza', csg.get('china_cherry_approved')),
            ('Figura en listado de mosca', csg.get('mosca_campaign_found')),
            ('Campaña vigente', csg.get('mosca_campaign_current')),
            ('Descolgado para China', csg.get('descolgado_china')),
        ]
        if csp_code:
            verification_rows.extend([
                ('CSP inscrito para China', csp.get('china_registered')),
                ('CSP aprobado por SAG', csp.get('china_approved')),
            ])
        else:
            verification_rows.append(('CSP', 'NO INGRESADO'))
        verification_panel = _panel('ESTADO DE VERIFICACIÓN', verification_rows, usable_width * 0.56, styles, GREEN, status_rows=True)

        varieties = ', '.join(csg.get('varieties') or []) or 'No verificadas'
        orchard_rows = [
            ('Productor', csg.get('producer_name') or 'No verificado'),
            ('Predio / establecimiento', csg.get('establishment_name') or 'No verificado'),
            ('Especie', 'CEREZA'),
            ('Variedades', varieties),
            ('Producto ChinaPort', csg.get('chinaport_product_name') or 'No verificado'),
            ('Nombre científico', csg.get('chinaport_scientific_name') or 'No verificado'),
        ]
        orchard_panel = _panel('DATOS DEL HUERTO', orchard_rows, usable_width * 0.44, styles, BLUE)
        main_panels = Table(
            [[verification_panel, orchard_panel]],
            colWidths=[usable_width * 0.56, usable_width * 0.44],
            hAlign='LEFT',
        )
        main_panels.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (0, 0), 0),
            ('RIGHTPADDING', (0, 0), (0, 0), 5),
            ('LEFTPADDING', (1, 0), (1, 0), 5),
            ('RIGHTPADDING', (1, 0), (1, 0), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
        ]))

    csp_panel = _csp_panel(csps, usable_width * 0.39, styles)
    campaign_panel = _campaign_panel(results, usable_width * 0.61, styles)
    bottom_panels = Table(
        [[campaign_panel, csp_panel]],
        colWidths=[usable_width * 0.61, usable_width * 0.39],
        hAlign='LEFT',
    )
    bottom_panels.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, 0), 0),
        ('RIGHTPADDING', (0, 0), (0, 0), 5),
        ('LEFTPADDING', (1, 0), (1, 0), 5),
        ('RIGHTPADDING', (1, 0), (1, 0), 0),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
    ]))

    source_status = '  ·  '.join(
        f"{source.get('name', '-')}:{str(source.get('status', 'unverified')).upper()}"
        for source in sources
    ) or 'Fuentes no consultadas'
    source_footer = Paragraph(escape(source_status), styles['small'])
    story = [
        header,
        Spacer(1, 14),
        main_panels,
        Spacer(1, 14),
        bottom_panels,
        Spacer(1, 14),
        _descolgados_panel(report, csgs, usable_width, styles),
        Spacer(1, 12),
        source_footer,
    ]

    fit = KeepInFrame(usable_width, usable_height, story, mode='shrink', hAlign='LEFT', vAlign='TOP')
    document.build([fit])
    return buffer.getvalue()


def build_validation_pdf(report, results, sources):
    csgs = results.get('csgs') or ([results.get('csg')] if results.get('csg') else [])
    csps = results.get('csps') or ([results.get('csp')] if results.get('csp', {}).get('code') else [])
    csg_page_groups = [csgs[index:index + 2] for index in range(0, len(csgs), 2)] or [[]]
    csp_page_groups = [csps[index:index + 4] for index in range(0, len(csps), 4)] or [[]]
    page_count = max(len(csg_page_groups), len(csp_page_groups))
    if page_count == 1:
        return _build_validation_pdf_page(report, results, sources)

    from pypdf import PdfReader, PdfWriter

    writer = PdfWriter()
    for page_index in range(page_count):
        page_csgs = csg_page_groups[page_index] if page_index < len(csg_page_groups) else []
        page_csps = csp_page_groups[page_index] if page_index < len(csp_page_groups) else []
        page_results = dict(results)
        page_results['csgs'] = page_csgs
        page_results['csg'] = page_csgs[0] if page_csgs else {}
        page_results['csps'] = page_csps
        page_results['csp'] = page_csps[0] if page_csps else {}
        page_report = SimpleNamespace(
            pk=report.pk,
            csg=page_csgs[0].get('code', '') if page_csgs else '',
            csp=page_csps[0].get('code', '') if page_csps else '',
            page_indicator=f'Página {page_index + 1} de {page_count}',
        )
        writer.append(PdfReader(BytesIO(_build_validation_pdf_page(page_report, page_results, sources))))

    output = BytesIO()
    writer.write(output)
    return output.getvalue()