import os
import re
import unicodedata
import json
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright

from .rules import summarize_campaign_rows, summarize_chinaport_rows, summarize_descolgados


SRA_SEARCH_URL = (
    'https://sra.sag.gob.cl/SRA_COMUNES/SRA_ContComunExt.asp?opcMenu=BusCodSAG'
)
CHINA_PBI_URL = os.getenv(
    'SAG_CHINA_PBI_URL',
    'https://app.powerbi.com/view?r=eyJrIjoiNGUxM2QwNmEtZGFiYS00M2Q1LTgyNjYtYzJkZjIyMDlmNGFmIiwidCI6Ijc3ZWNkYTc1LTU4NjQtNDIyYS1hNTM1LTZlYTY3MTU0MDI5YyIsImMiOjl9',
)
MOSCA_PBI_URL = os.getenv(
    'SAG_MOSCA_PBI_URL',
    'https://app.powerbi.com/view?r=eyJrIjoiYjAwY2VkMmYtYzU0Mi00NjhjLTg0MTYtYTgyYmM2OTcyZjdjIiwidCI6Ijc3ZWNkYTc1LTU4NjQtNDIyYS1hNTM1LTZlYTY3MTU0MDI5YyIsImMiOjl9',
)
CHINAPORT_URL = (
    'https://scintl.chinaport.gov.cn/aprwebserver/pages/apr/public/html/companyList.html'
)
DESCOLGADOS_LOGIN_URL = 'https://descolgados.sag.gob.cl/login.asp'
DESCOLGADOS_LIST_URL = 'https://descolgados.sag.gob.cl/SQL_Descolga_LEFTlist.asp'


def _normal(value):
    value = unicodedata.normalize('NFKD', str(value or ''))
    value = ''.join(char for char in value if not unicodedata.combining(char))
    return ' '.join(value.upper().split())


def _get_table_rows(page):
    records = []
    for row in page.get_by_role('row').all():
        cells = row.get_by_role('gridcell').all_text_contents()
        if not cells:
            cells = row.locator('th, td').all_inner_texts()
        cells = [cell.strip() for cell in cells]
        if cells:
            records.append(cells)
    return records


def _exact_record(records, code):
    normalized_code = str(code).strip()
    for cells in records:
        if cells and cells[0].strip() == normalized_code:
            return cells
        if len(cells) > 1 and cells[1].strip() == normalized_code:
            return cells
    return None


def parse_cherry_species(species_lines):
    species = []
    varieties = []
    for item in species_lines:
        parts = re.split(r'\s+-\s+', item, maxsplit=1)
        if len(parts) != 2 or 'CEREZ' not in _normal(parts[0]):
            continue
        if 'CEREZA' not in species:
            species.append('CEREZA')
        variety = parts[1].strip()
        if variety and variety not in varieties:
            varieties.append(variety)
    return species, varieties


def _map_powerbi_row(headers, cells, code, code_column):
    header_map = {_normal(header): index for index, header in enumerate(headers)}
    code_index = header_map.get(_normal(code_column))
    if code_index is None:
        raise RuntimeError('No se encontró la columna del código solicitado.')

    match = next((row for row in [cells] if code_index < len(row) and row[code_index].strip() == code), None)
    if not match:
        return {'found': False, 'code': code, 'region': '', 'commune': '', 'establishment_name': ''}

    def value_for(header):
        index = header_map.get(_normal(header))
        return match[index].strip() if index is not None and index < len(match) else ''

    return {
        'found': True,
        'code': code,
        'establishment_name': value_for('NOMBRE ESTABLECIMIENTO'),
        'region': value_for('REGION'),
        'commune': value_for('COMUNA'),
    }


def _source_failure(name, message='La fuente no pudo verificarse desde el servidor.'):
    return {'name': name, 'status': 'unavailable', 'message': message}


def _query_sra(page, code):
    page.goto(SRA_SEARCH_URL, wait_until='domcontentloaded', timeout=30000)
    page.locator('#buscaPorTip2').check()
    page.get_by_role('textbox').fill(code)
    with page.expect_response(
        lambda response: 'SRA_ContComunExt.asp' in response.url
        and response.request.method == 'POST',
        timeout=20000,
    ) as response_info:
        page.get_by_role('button', name='Buscar', exact=True).click()
    response = response_info.value
    if response.status >= 400:
        raise RuntimeError('SRA respondió con error HTTP.')
    page.get_by_role('columnheader', name='Código SAG').wait_for(timeout=15000)
    rows = page.get_by_role('row').all()
    match = None
    for row in rows:
        cells = row.locator('td').all_inner_texts()
        if cells and cells[0].strip().startswith(code):
            match = [cell.strip() for cell in cells]
            break
    if not match:
        return {
            'found': False,
            'active': False,
            'producer_name': '',
            'establishment_name': '',
            'address': '',
            'species': [],
            'varieties': [],
        }

    status_text = _normal(match[0])
    species_lines = page.get_by_role('row').filter(has_text=re.compile(rf'\b{re.escape(code)}\b')).first.locator('td').nth(3).locator('li').all_text_contents()
    species, varieties = parse_cherry_species(species_lines)

    return {
        'found': True,
        'active': '(ACTIVO)' in status_text and '(INACTIVO)' not in status_text,
        'producer_name': match[2] if len(match) > 2 else '',
        'establishment_name': match[1].split('Dirección:')[0].strip() if len(match) > 1 else '',
        'address': match[1].split('Dirección:', 1)[1].strip() if len(match) > 1 and 'Dirección:' in match[1] else '',
        'species': species,
        'varieties': varieties,
    }


def _select_powerbi_tab(page, tab_name):
    button = page.get_by_role('button', name=tab_name, exact=True)
    button.wait_for(state='visible', timeout=45000)
    if button.get_attribute('aria-pressed') != 'true':
        button.click(force=True, timeout=10000)
    page.wait_for_timeout(700)


def _search_powerbi_code(page, code):
    sandbox = next((frame for frame in page.frames if frame.name == 'visual-sandbox'), None)
    if sandbox is None:
        raise RuntimeError('No se encontró el control de búsqueda del informe.')
    search = sandbox.get_by_role('textbox', name='Enter your search')
    search.fill(code)
    search.press('Enter')
    page.wait_for_timeout(900)
    return _get_table_rows(page)


def _query_china_powerbi(page, report_url, code, tab_name, code_column):
    if 'app.powerbi.com/view' not in page.url:
        page.goto(report_url, wait_until='domcontentloaded', timeout=45000)
    _select_powerbi_tab(page, tab_name)
    records = _search_powerbi_code(page, code)
    headers = [header.strip() for header in page.get_by_role('columnheader').all_text_contents()]
    mapped_rows = [_map_powerbi_row(headers, row, code, code_column) for row in records]
    return next((row for row in mapped_rows if row['found']), {
        'found': False,
        'code': code,
        'region': '',
        'commune': '',
        'establishment_name': '',
    })


def _query_mosca_tab(page, report_url, code, tab_name):
    if 'app.powerbi.com/view' not in page.url:
        page.goto(report_url, wait_until='domcontentloaded', timeout=45000)
    _select_powerbi_tab(page, tab_name)
    records = _search_powerbi_code(page, code)
    headers = [header.strip() for header in page.get_by_role('columnheader').all_text_contents()]
    header_map = {_normal(header): index for index, header in enumerate(headers)}
    code_index = next((index for name, index in header_map.items() if name == _normal(tab_name)), None)
    if code_index is None:
        raise RuntimeError('No se reconocieron las columnas de la tabla de campañas.')

    matching_rows = []
    for cells in records:
        if code_index < len(cells) and cells[code_index].strip() == code:
            matching_rows.append(cells)

    current_index = next((index for name, index in header_map.items() if 'CAMPANA VIGENTE' in name), None)
    campaign_index = next((index for name, index in header_map.items() if name == 'CAMPANA'), None)
    country_index = next((index for name, index in header_map.items() if name == 'PAIS'), None)
    if current_index is None or campaign_index is None or country_index is None:
        raise RuntimeError('La tabla de campañas no incluye campaña, país y vigencia.')

    mapped = []
    for cells in matching_rows:
        mapped.append({
            'campaign': cells[campaign_index] if campaign_index < len(cells) else '',
            'country': cells[country_index] if country_index < len(cells) else '',
            'current': cells[current_index] if current_index < len(cells) else '',
        })
    summary = summarize_campaign_rows(mapped)
    return {'found': summary['found'], 'current': summary['current'], 'campaigns': summary['campaigns']}


def _login_descolgados(page):
    username = os.getenv('DESCOLGADOS_USERNAME', '').strip()
    password = os.getenv('DESCOLGADOS_PASSWORD', '')
    if not username or not password:
        return False

    page.goto(DESCOLGADOS_LOGIN_URL, wait_until='domcontentloaded', timeout=30000)
    if page.locator('#username').count() == 0:
        return 'LISTADO DE DETECCIONES TEMPORADA' in page.locator('body').inner_text()
    page.locator('#username').fill(username)
    page.locator('#password').fill(password)
    page.locator('#submit').click()
    try:
        page.get_by_text('LISTADO DE DETECCIONES TEMPORADA', exact=False).wait_for(timeout=15000)
    except PlaywrightTimeoutError:
        return False
    return True


def _query_descolgados(page, csg):
    if not _login_descolgados(page):
        return None
    params = urlencode({
        't': 'SQL_Descolga_LEFT',
        'psearch': csg,
        'Submit': 'BUSCAR (*)',
        'psearchtype': '',
    })
    response = page.goto(
        f'{DESCOLGADOS_LIST_URL}?{params}',
        wait_until='domcontentloaded',
        timeout=30000,
    )
    if response and response.status >= 400:
        raise RuntimeError('Descolgados respondió con error HTTP.')
    page.get_by_text('LISTADO DE DETECCIONES TEMPORADA', exact=False).wait_for(timeout=15000)
    if page.get_by_text('NO SE ENCONTRARON REGISTROS', exact=False).count() > 0:
        return summarize_descolgados([], csg)
    headers = [header.strip() for header in page.get_by_role('cell').all_text_contents()]
    header_text = ' '.join(headers)
    if 'Nombre Especie' not in header_text or 'País a Descolgar' not in header_text:
        raise RuntimeError('La tabla de Descolgados no contiene las columnas esperadas.')

    data = []
    for row in page.get_by_role('row').all():
        cells = [cell.strip() for cell in row.locator('td').all_inner_texts()]
        if len(cells) < 13 or cells[5].strip() != csg:
            continue
        data.append(map_descolgados_cells(cells))
    return summarize_descolgados(data, csg)


def map_descolgados_cells(cells):
    return {
        'csg': cells[5],
        'species': cells[7],
        'variety': cells[8],
        'country_detected': cells[10],
        'country_to_remove': cells[11],
        'pest': cells[12],
    }


def _query_chinaport(page, code):
    try:
        page.goto(CHINAPORT_URL, wait_until='domcontentloaded', timeout=25000)
    except PlaywrightTimeoutError:
        return {'verified': False, 'found': None, 'reason': 'ChinaPort no respondió desde el servidor.'}

    confirm = page.get_by_role('button', name=re.compile(r'Confirm|确认', re.I))
    if confirm.count():
        confirm.first.click(force=True, timeout=5000)
        page.wait_for_timeout(400)

    registration_field = page.locator('#overseasOfficialRegNo')
    query_button = page.locator('#queryBtn')
    if registration_field.count() == 0 or query_button.count() == 0:
        return {'verified': False, 'found': None, 'reason': 'No se identificó el formulario de consulta ChinaPort.'}

    registration_field.fill(code)

    def is_code_query(response):
        if '/publicity/list' not in response.url or response.request.method != 'POST':
            return False
        try:
            body = json.loads(response.request.post_data or '{}')
        except (TypeError, ValueError):
            return False
        submitted_code = str(body.get('overseasOfficialRegNo', '')).strip().strip('%').strip()
        return submitted_code == str(code).strip()

    try:
        with page.expect_response(is_code_query, timeout=20000) as response_info:
            query_button.click(force=True)
        response = response_info.value
    except PlaywrightTimeoutError:
        return {'verified': False, 'found': None, 'reason': 'ChinaPort no respondió a la búsqueda del código.'}

    if response.status >= 400:
        return {'verified': False, 'found': None, 'reason': 'ChinaPort respondió con error HTTP.'}
    payload = response.json()
    if payload.get('code') != 200:
        return {'verified': False, 'found': None, 'reason': 'ChinaPort devolvió un estado de consulta no exitoso.'}
    rows = payload.get('data', {}).get('rows', [])
    return summarize_chinaport_rows(rows, code)


def _run_single_cherry_china_check(csg='', csp='', csps=None, context=None, pages=None):
    try:
        from dotenv import load_dotenv
        load_dotenv(Path(settings.BASE_DIR).parent / '.env', override=False)
    except ImportError:
        pass

    csp_codes = list(dict.fromkeys(str(code).strip() for code in (csps if csps is not None else ([csp] if csp else [])) if str(code).strip()))
    results = {
        'csg': {'code': csg or '', 'active': None, 'producer_name': '', 'establishment_name': '', 'species': [], 'varieties': [], 'china_registered': None, 'china_approved': None, 'mosca_campaign_found': None, 'mosca_campaign_current': None, 'mosca_campaigns': [], 'descolgado_china': None, 'descolgados': []},
        'csp': {'code': csp_codes[0] if csp_codes else '', 'china_registered': None, 'china_approved': None, 'mosca_campaign_found': None, 'mosca_campaign_current': None, 'mosca_campaigns': []},
        'csps': [],
        'chinaport': {'csg': None, 'csp': None},
    }
    sources = []

    owns_context = context is None
    playwright = None
    browser = None
    if owns_context:
        playwright = sync_playwright().start()
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(locale='es-CL', viewport={'width': 1800, 'height': 1100})

    owns_pages = pages is None
    try:
        if pages is None:
            pages = (context.new_page(), context.new_page(), context.new_page())
        page, china_page, mosca_page = pages
        for source_page in pages:
            source_page.set_default_timeout(18000)

        if csg:
            try:
                sra = _query_sra(page, csg)
                results['csg'].update({key: sra[key] for key in ('active', 'producer_name', 'establishment_name', 'species', 'varieties')})
                sources.append({'name': 'SRA', 'status': 'ok', 'found': sra['found']})
            except Exception:
                sources.append(_source_failure('SRA'))
        if csg:
            try:
                csg_result = _query_china_powerbi(china_page, CHINA_PBI_URL, csg, 'CSG Inscritos', 'CSG')
                results['csg']['china_registered'] = csg_result['found']
                results['csg'].update({key: csg_result[key] for key in ('region', 'commune') if key in csg_result})
                sources.append({'name': 'China-CSG', 'status': 'ok', 'found': csg_result['found']})
            except Exception:
                sources.append(_source_failure('China-CSG'))
        csp_results_by_code = {}
        for csp_code in csp_codes:
            csp_result = {
                'code': csp_code,
                'china_registered': None,
                'china_approved': None,
                'mosca_campaign_found': None,
                'mosca_campaign_current': None,
                'mosca_campaigns': [],
            }
            try:
                registered = _query_china_powerbi(china_page, CHINA_PBI_URL, csp_code, 'CSP Inscritos', 'CSP')
                csp_result['china_registered'] = registered['found']
                approved = _query_china_powerbi(china_page, CHINA_PBI_URL, csp_code, 'CSP Aprobados', 'CSP')
                csp_result['china_approved'] = approved['found']
                sources.append({'name': 'China-CSP', 'status': 'ok', 'found': registered['found'] or approved['found'], 'codes': [csp_code]})
            except Exception:
                sources.append(_source_failure('China-CSP'))
            csp_results_by_code[csp_code] = csp_result

        if csg:
            try:
                mosca = _query_mosca_tab(mosca_page, MOSCA_PBI_URL, csg, 'CSG')
                results['csg']['mosca_campaign_found'] = mosca['found']
                results['csg']['mosca_campaign_current'] = mosca['current']
                results['csg']['mosca_campaigns'] = mosca['campaigns']
                sources.append({'name': 'Mosca-CSG', 'status': 'ok', 'found': mosca['found']})
            except Exception:
                sources.append(_source_failure('Mosca-CSG'))
        for csp_code in csp_codes:
            csp_result = csp_results_by_code[csp_code]
            try:
                mosca = _query_mosca_tab(mosca_page, MOSCA_PBI_URL, csp_code, 'CSP')
                csp_result['mosca_campaign_found'] = mosca['found']
                csp_result['mosca_campaign_current'] = mosca['current']
                csp_result['mosca_campaigns'] = mosca['campaigns']
                sources.append({'name': 'Mosca-CSP', 'status': 'ok', 'found': mosca['found'], 'codes': [csp_code]})
            except Exception:
                sources.append(_source_failure('Mosca-CSP'))
            results['csps'].append(csp_result)
        if results['csps']:
            results['csp'] = results['csps'][0]

        if csg:
            try:
                descolgados = _query_descolgados(page, csg)
                if descolgados is None:
                    sources.append(_source_failure('Descolgados', 'No están configuradas las credenciales del servicio.'))
                else:
                    results['csg']['descolgado_china'] = descolgados['descolgado_china']
                    results['csg']['descolgados'] = descolgados['detections']
                    sources.append({'name': 'Descolgados', 'status': 'ok', 'found': descolgados['descolgado_china']})
            except Exception:
                sources.append(_source_failure('Descolgados'))

        if csg:
            chinaport = _query_chinaport(page, csg)
            results['csg']['china_cherry_approved'] = chinaport.get('china_cherry_approved')
            results['csg']['chinaport_product_name'] = chinaport.get('product_name', '')
            results['csg']['chinaport_scientific_name'] = chinaport.get('scientific_name', '')
            results['csg']['chinaport_registration_status'] = chinaport.get('registration_status', '')
            results['csg']['chinaport_registration_expiry'] = chinaport.get('registration_expiry', '')
            sources.append({
                'name': 'ChinaPort-CSG',
                'status': 'ok' if chinaport.get('verified') else 'unverified',
                'found': chinaport.get('found'),
            })
    finally:
        if owns_pages:
            for source_page in pages:
                source_page.close()
        if owns_context:
            context.close()
            browser.close()
            playwright.stop()

    return results, sources


def run_cherry_china_checks(csg='', csp='', csgs=None, csps=None):
    raw_codes = csgs if csgs is not None else ([csg] if csg else [])
    codes = list(dict.fromkeys(str(code).strip() for code in raw_codes if str(code).strip()))
    raw_csps = csps if csps is not None else ([csp] if csp else [])
    csp_codes = list(dict.fromkeys(str(code).strip() for code in raw_csps if str(code).strip()))

    checks = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True, args=['--no-sandbox', '--disable-setuid-sandbox'])
        context = browser.new_context(locale='es-CL', viewport={'width': 1800, 'height': 1100})
        pages = (context.new_page(), context.new_page(), context.new_page())
        try:
            if codes:
                for index, code in enumerate(codes):
                    checks.append(_run_single_cherry_china_check(
                        code,
                        csp_codes[0] if csp_codes and index == 0 else '',
                        csps=csp_codes if index == 0 else [],
                        context=context,
                        pages=pages,
                    ))
            else:
                checks.append(_run_single_cherry_china_check(
                    '', csp_codes[0] if csp_codes else '', csps=csp_codes, context=context, pages=pages
                ))
        finally:
            for page in pages:
                page.close()
            context.close()
            browser.close()

    csg_results = [check[0].get('csg') or {} for check in checks if check[0].get('csg', {}).get('code')]
    source_entries = {}
    for check_index, (_, source_list) in enumerate(checks):
        for source in source_list:
            name = source.get('name', 'Fuente')
            source_entries.setdefault(name, []).append((check_index, source))

    merged_sources = []
    for name, entries in source_entries.items():
        statuses = [entry.get('status', 'unavailable') for _, entry in entries]
        if all(source_status == 'ok' for source_status in statuses):
            merged_status = 'ok'
        elif any(source_status == 'ok' for source_status in statuses):
            merged_status = 'partial'
        else:
            merged_status = 'unverified'
        merged = {
            'name': name,
            'status': merged_status,
            'codes': (csp_codes if name.endswith('-CSP') else [codes[index] for index, _ in entries if index < len(codes)]),
        }
        found_values = [entry['found'] for _, entry in entries if 'found' in entry]
        if found_values:
            merged['found'] = any(value is True for value in found_values) if len(found_values) == 1 else found_values
        merged_sources.append(merged)

    first_results = checks[0][0]
    csp_results = first_results.get('csps') or ([first_results.get('csp')] if first_results.get('csp', {}).get('code') else [])
    results = {
        'csg': csg_results[0] if csg_results else first_results.get('csg', {}),
        'csgs': csg_results,
        'csp': csp_results[0] if csp_results else first_results.get('csp', {}),
        'csps': csp_results,
        'chinaport': [check[0].get('chinaport', {}) for check in checks if check[0].get('csg', {}).get('code')],
    }
    return results, merged_sources