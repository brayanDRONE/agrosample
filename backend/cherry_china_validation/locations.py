import csv
import re
import unicodedata
from functools import lru_cache
from pathlib import Path


def _normalize(value):
    text = unicodedata.normalize('NFKD', str(value or ''))
    text = ''.join(char for char in text if not unicodedata.combining(char))
    return ' '.join(re.findall(r'[A-Z0-9]+', text.upper()))


@lru_cache(maxsize=1)
def _territorial_codes():
    # SUBDERE, CUT 2018: https://www.subdere.gov.cl/documentacion/códigos-únicos-territoriales-actualizados-al-06-de-septiembre-2018
    with (Path(__file__).parent / 'territorial_codes.csv').open(encoding='utf-8', newline='') as source:
        return list(csv.DictReader(source))


def _region_matches(actual, official):
    actual = _normalize(actual)
    official = _normalize(official)
    if not actual:
        return True
    if official == 'METROPOLITANA DE SANTIAGO' and actual in ('RM', 'REGION METROPOLITANA', 'METROPOLITANA'):
        return True
    ignored = {'DE', 'DEL', 'LA', 'EL', 'LOS', 'LAS', 'Y', 'O', 'GENERAL', 'GRAL', 'REGION'}
    official_words = set(official.split()) - ignored
    actual_words = set(actual.split()) - ignored
    return bool(official_words) and official_words <= actual_words


def _lookup(commune, region=''):
    normalized_commune = _normalize(commune)
    if not normalized_commune:
        return None
    matches = [
        row for row in _territorial_codes()
        if _normalize(row['commune']) == normalized_commune
        and _region_matches(region, row['region'])
    ]
    return matches[0] if len(matches) == 1 else None


def resolve_location(sra_address='', powerbi_commune='', powerbi_region=''):
    parts = [part.strip() for part in sra_address.split(',')]
    sra_location = _lookup(parts[-2], parts[-1]) if len(parts) >= 2 else None
    powerbi_location = _lookup(powerbi_commune, powerbi_region)

    if sra_location and powerbi_commune and _normalize(sra_location['commune']) != _normalize(powerbi_commune):
        return {'commune': '', 'province': ''}
    if sra_location and powerbi_location and sra_location != powerbi_location:
        return {'commune': '', 'province': ''}
    location = sra_location or (powerbi_location if not sra_address else None)
    return {
        'commune': location['commune'] if location else '',
        'province': location['province'] if location else '',
    }
