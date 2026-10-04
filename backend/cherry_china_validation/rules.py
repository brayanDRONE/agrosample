import re
import unicodedata
from datetime import date, datetime


def normalize_text(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(text.upper().split())


def is_cherry(species):
    return 'CEREZ' in normalize_text(species)


def includes_china(country_text):
    return bool(re.search(r'\bCHINA\b', normalize_text(country_text)))


def summarize_campaign_rows(rows):
    campaigns = []
    seen = set()
    for row in rows:
        current = normalize_text(row.get('current')) in {'SI', 'YES', 'TRUE', '1'}
        if not current:
            continue
        campaign = str(row.get('campaign') or '').strip()
        country = str(row.get('country') or '').strip()
        key = (normalize_text(campaign), normalize_text(country))
        if key not in seen:
            seen.add(key)
            campaigns.append({'campaign': campaign, 'country': country})
    return {
        'found': bool(rows),
        'current': bool(campaigns),
        'campaigns': campaigns,
    }


def summarize_descolgados(rows, csg):
    matching_rows = [
        row for row in rows
        if str(row.get('csg', '')).strip() == str(csg).strip()
        and is_cherry(row.get('species'))
        and includes_china(row.get('country_to_remove'))
    ]
    detections = []
    seen = set()
    for row in matching_rows:
        item = {
            'variety': str(row.get('variety') or '').strip(),
            'pest': str(row.get('pest') or '').strip(),
            'target_country': str(row.get('country_to_remove') or '').strip(),
        }
        key = tuple(normalize_text(item[field]) for field in ('variety', 'pest', 'target_country'))
        if key not in seen:
            seen.add(key)
            detections.append(item)
    return {'descolgado_china': bool(detections), 'detections': detections}


def summarize_chinaport_rows(rows, csg, today=None):
    today = today or date.today()
    matches = [
        row for row in rows
        if str(row.get('overseasOfficialRegNo', '')).strip() == str(csg).strip()
    ]
    if not matches:
        return {
            'verified': True,
            'found': False,
            'china_cherry_approved': False,
            'product_name': '',
            'scientific_name': '',
            'registration_status': '',
            'registration_expiry': '',
        }

    row = matches[0]
    product_name, scientific_name = _cherry_product_pair(row)
    status_text = _normalize_text(row.get('regStateNameEn') or row.get('regStateNameCn') or row.get('regState'))
    active = (
        str(row.get('regState')) == '1'
        or 'NORMAL' in status_text
        or '有效' in status_text
    ) and not any(term in status_text for term in ('SUSPENSION', 'CANCELLATION', 'INVALID', '暂停', '注销', '失效'))
    registration_state = row.get('regStateNameEn') or row.get('regStateNameCn') or {
        '1': 'Normal (vigente)',
        '2': 'Suspensión',
        '3': 'Cancelado',
        '4': 'Inválido',
    }.get(str(row.get('regState')), status_text)

    def parse_date(value):
        if not value:
            return None
        try:
            return datetime.strptime(str(value)[:10], '%Y-%m-%d').date()
        except ValueError:
            return None

    valid_from = parse_date(row.get('validFrom'))
    valid_to = parse_date(row.get('validTo'))
    date_valid = (valid_from is None or valid_from <= today) and (valid_to is None or today <= valid_to)
    cherry = bool(product_name)

    return {
        'verified': True,
        'found': True,
        'china_cherry_approved': cherry and active and date_valid,
        'product_name': product_name,
        'scientific_name': scientific_name,
        'registration_status': registration_state,
        'registration_expiry': row.get('validTo') or '',
    }


def _cherry_product_pair(row):
    english_names = _split_product_values(row.get('prodNameEn'))
    chinese_names = _split_product_values(row.get('prodNameCn'))
    scientific_names = _split_product_values(row.get('prodNameLa'))

    cherry_index = next(
        (index for index, name in enumerate(english_names) if _normalize_text(name) == 'CHERRY'),
        None,
    )
    if cherry_index is None:
        cherry_index = next(
            (index for index, name in enumerate(chinese_names) if '樱桃' in name or '櫻桃' in name),
            None,
        )
    if cherry_index is None:
        return '', ''

    cherry_scientific_names = {'PRUNUS AVIUM', 'PRUNUS CERASUS'}
    scientific_name = next(
        (name for name in scientific_names if _normalize_text(name) in cherry_scientific_names),
        '',
    )
    return 'Cherry', scientific_name


def _split_product_values(value):
    return [
        item.strip()
        for item in re.split(r'[\r\n,;，；]+', str(value or ''))
        if item.strip()
    ]


def _normalize_text(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(text.upper().split())