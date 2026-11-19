import logging
from datetime import timedelta

from django.db import models, transaction
from django.utils import timezone
from inspections.models import Establishment, EstablishmentPlan
from inspections.plan_usage import finish_usage, plan_summary

from .models import CherryChinaReport
from .pdf import build_validation_pdf
from .sources import run_cherry_china_checks


logger = logging.getLogger(__name__)


def claim_next_report():
    cutoff = timezone.now() - timedelta(hours=1)
    stale_establishments = CherryChinaReport.objects.filter(
        status__in=['QUEUED', 'PROCESSING'], plan_usage__isnull=False,
    ).filter(
        models.Q(status='QUEUED', created_at__lt=cutoff) |
        models.Q(status='PROCESSING', started_at__lt=cutoff)
    ).values_list('plan_usage__establishment_id', flat=True).distinct()
    for plan in EstablishmentPlan.objects.filter(establishment_id__in=stale_establishments):
        plan_summary(plan)
    CherryChinaReport.objects.filter(
        plan_usage__isnull=True, status='PROCESSING', started_at__lt=cutoff,
    ).update(
        status='FAILED', error_message='La consulta excedió el tiempo de espera. Inténtalo nuevamente.',
        completed_at=timezone.now(),
    )
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
        if not any(source.get('status') in ('ok', 'partial') for source in sources):
            raise RuntimeError('No fue posible verificar ninguna fuente oficial.')

        with transaction.atomic():
            if report.plan_usage_id:
                Establishment.objects.select_for_update().get(pk=report.plan_usage.establishment_id)
            report = CherryChinaReport.objects.select_for_update().get(pk=report.pk)
            if report.status != 'PROCESSING':
                return report
            if not finish_usage(report.plan_usage, True):
                raise RuntimeError('La reserva de uso fue cancelada.')
            report.results = results
            report.sources = sources
            report.status = 'COMPLETED'
            report.completed_at = timezone.now()
            report.save(update_fields=['results', 'sources', 'status', 'completed_at'])
    except Exception:
        logger.exception('[CEREZA CHINA] Fallo al procesar informe %s', report.pk)
        with transaction.atomic():
            if report.plan_usage_id:
                Establishment.objects.select_for_update().get(pk=report.plan_usage.establishment_id)
            report = CherryChinaReport.objects.select_for_update().get(pk=report.pk)
            if report.status != 'PROCESSING':
                return report
            finish_usage(report.plan_usage, False)
            report.status = 'FAILED'
            report.error_message = 'La consulta no pudo completarse.'
            report.completed_at = timezone.now()
            report.save(update_fields=['status', 'error_message', 'completed_at'])
        return report
    try:
        report.pdf_data = build_validation_pdf(report, results, sources)
        report.save(update_fields=['pdf_data'])
    except Exception:
        logger.exception('[CEREZA CHINA] No se pudo generar el PDF del informe %s', report.pk)
    return report