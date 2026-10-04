import logging

from django.db import transaction
from django.utils import timezone

from .models import CherryChinaReport
from .pdf import build_validation_pdf
from .sources import run_cherry_china_checks


logger = logging.getLogger(__name__)


def claim_next_report():
    with transaction.atomic():
        report = (
            CherryChinaReport.objects.select_for_update(skip_locked=True)
            .filter(status='QUEUED')
            .order_by('created_at', 'pk')
            .first()
        )
        if report is None:
            return None

        report.status = 'PROCESSING'
        report.started_at = timezone.now()
        report.attempts += 1
        report.save(update_fields=['status', 'started_at', 'attempts'])
        return report.pk


def process_report(report_id):
    report = CherryChinaReport.objects.get(pk=report_id)
    try:
        results, sources = run_cherry_china_checks(
            csg=report.csg,
            csp=report.csp,
            csgs=report.csgs,
            csps=report.csps,
        )
        if not any(source.get('status') == 'ok' for source in sources):
            raise RuntimeError('No fue posible verificar ninguna fuente oficial.')

        report.results = results
        report.sources = sources
        pdf_bytes = build_validation_pdf(report, results, sources)
        report.pdf_data = pdf_bytes
        report.status = 'COMPLETED'
        report.completed_at = timezone.now()
        report.save()
        return report
    except Exception:
        logger.exception('[CEREZA CHINA] Fallo al procesar informe %s', report.pk)
        report.status = 'FAILED'
        report.error_message = 'La consulta no pudo completarse.'
        report.completed_at = timezone.now()
        report.save(update_fields=['status', 'error_message', 'completed_at'])
        return report