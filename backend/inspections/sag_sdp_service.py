"""Cliente y parser para consultas de sitios de produccion SAG-USA."""

import logging
import re
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, build_opener, HTTPCookieProcessor
from http.cookiejar import CookieJar


logger = logging.getLogger(__name__)

SAG_SDP_URL = 'https://sispusa.sag.gob.cl/pubsber/reporteSDPver3.asp'


class _TableParser(HTMLParser):
    """Extrae filas y celdas sin depender de la estructura visual completa."""

    def __init__(self):
        super().__init__()
        self.rows = []
        self._row = None
        self._cell = None
        self._text = []

    def handle_starttag(self, tag, attrs):
        if tag == 'tr':
            self._row = []
        elif tag in {'td', 'th'} and self._row is not None:
            self._cell = tag
            self._text = []
        elif tag == 'br' and self._cell is not None:
            self._text.append(' ')

    def handle_data(self, data):
        if self._cell is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag in {'td', 'th'} and self._cell is not None:
            self._row.append(' '.join(''.join(self._text).split()))
            self._cell = None
            self._text = []
        elif tag == 'tr' and self._row is not None:
            if self._row:
                self.rows.append(self._row)
            self._row = None


def _parse_sdp_cell(text):
    match = re.search(r'SDP\s*:\s*(.*?)(?:\s*\(([^)]*)\))?$', text, re.IGNORECASE)
    if not match:
        return '', None

    sdp = match.group(1).strip()
    area = None
    if match.group(2):
        area_match = re.search(r'(\d+(?:[.,]\d+)?)\s*ha', match.group(2), re.IGNORECASE)
        if area_match:
            area = float(area_match.group(1).replace(',', '.'))
    return sdp, area


def _parse_sag_row(row):
    if len(row) < 6:
        return None

    combined = ' '.join(row)
    code_match = re.search(r'(?<!\d)(\d{5,})(?!\d)', row[0])
    sdp, surface = _parse_sdp_cell(row[0])
    if not code_match or not sdp:
        return None

    species_variety = row[3].strip()
    species, separator, variety = species_variety.partition('.')
    authorized = row[2].strip().upper()
    region_match = re.search(r'\d+', row[5])

    return {
        'codigo_sag': code_match.group(1),
        'sdp': sdp,
        'superficie_ha': surface,
        'productor': row[1].strip(),
        'muestreo_lote': authorized == 'SI',
        'autorizado_muestreo_lote': authorized,
        'especie': species.strip(),
        'variedad': variety.strip() if separator else '',
        'especie_variedad': species_variety,
        'comuna': row[4].strip(),
        'region': int(region_match.group(0)) if region_match else None,
        'raw_row': row,
        'raw_match': combined,
    }


def parse_sag_sdp_html(html):
    """Devuelve el primer registro SAG encontrado en una respuesta HTML."""
    parser = _TableParser()
    parser.feed(html or '')
    for row in parser.rows:
        parsed = _parse_sag_row(row)
        if parsed:
            return parsed
    return None


class SagSdpService:
    def __init__(self, timeout=15, session=None):
        self.timeout = timeout
        self.session = session or build_opener(HTTPCookieProcessor(CookieJar()))

    def query(self, sdp):
        """Consulta un SDP y devuelve status y datos estructurados."""
        normalized_sdp = str(sdp or '').strip()
        if not normalized_sdp or not normalized_sdp.isdigit():
            return {'status': 'INVALID_REQUEST', 'sdp_consultado': normalized_sdp, 'datos': None}

        logger.info('[SAG] Codigo consultado: %s', normalized_sdp)
        payload = {
            'BRIDREGION': '0',
            'BCODSAG': normalized_sdp,
            'BRCODSAG': 'Buscar',
            'BIDESP': '0',
            'BRIDCOMUNA': '0',
            'BNOMSDP': '',
        }

        try:
            request = Request(
                SAG_SDP_URL,
                data=urlencode(payload).encode('ascii'),
                headers={
                    'Accept': 'text/html,application/xhtml+xml',
                    'User-Agent': 'SIF-Digital-SAG/1.0',
                },
                method='POST',
            )
            with self.session.open(request, timeout=self.timeout) as response:
                charset = None
                if hasattr(response.headers, 'get_content_charset'):
                    charset = response.headers.get_content_charset()
                html = response.read().decode(charset or 'latin-1')
        except TimeoutError:
            logger.warning('[SAG] Resultado: TIMEOUT para %s', normalized_sdp)
            return {'status': 'TIMEOUT', 'sdp_consultado': normalized_sdp, 'datos': None}
        except (HTTPError, URLError, OSError):
            logger.exception('[SAG] Resultado: UNAVAILABLE para %s', normalized_sdp)
            return {'status': 'UNAVAILABLE', 'sdp_consultado': normalized_sdp, 'datos': None}

        data = parse_sag_sdp_html(html)
        if not data:
            logger.info('[SAG] Resultado: NOT_FOUND para %s', normalized_sdp)
            return {'status': 'NOT_FOUND', 'sdp_consultado': normalized_sdp, 'datos': None}

        logger.info('[SAG] Resultado: FOUND para %s', normalized_sdp)
        return {'status': 'FOUND', 'sdp_consultado': normalized_sdp, 'datos': data}