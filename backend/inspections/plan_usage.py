from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from .models import Establishment, EstablishmentPlan, PlanUsage


class PlanUsageError(Exception):
    pass


def establishment_for_user(user):
    if hasattr(user, 'establishment_admin'):
        return user.establishment_admin
    if hasattr(user, 'profile'):
        return user.profile.establishment
    return None


def _is_superadmin(user):
    return user.is_superuser or (hasattr(user, 'profile') and user.profile.is_superadmin())


def _expire_pro(plan, now):
    if plan.plan == 'PRO' and now >= plan.activated_at + timedelta(days=30):
        plan.plan = 'FREE'
        plan.activated_at = now
        plan.free_reset_at = None
        plan.alert_message = 'Tu plan Pro venció y ahora tienes el plan Free.'
        plan.save(update_fields=['plan', 'activated_at', 'free_reset_at', 'alert_message', 'updated_at'])


def _active_usages(plan, now):
    usages = PlanUsage.objects.filter(
        establishment=plan.establishment,
        plan=plan.plan,
        activation=plan.activated_at,
        status__in=['RESERVED', 'DISPATCHED', 'COMPLETED'],
    )
    if plan.plan == 'FREE':
        usages = usages.filter(
            Q(status__in=['RESERVED', 'DISPATCHED']) | Q(completed_at__gt=now - timedelta(hours=24))
        )
        if plan.free_reset_at:
            usages = usages.filter(created_at__gte=plan.free_reset_at)
    return usages


def _recover_china_reports(plan, now):
    from cherry_china_validation.models import CherryChinaReport

    stale = CherryChinaReport.objects.select_for_update().filter(
        plan_usage__establishment_id=plan.establishment_id,
    ).filter(
        Q(status='QUEUED', created_at__lt=now - timedelta(hours=1)) |
        Q(status='PROCESSING', started_at__lt=now - timedelta(hours=1))
    )
    for report in stale:
        if report.plan_usage.status == 'COMPLETED' and report.results and report.sources:
            report.status = 'COMPLETED'
            report.error_message = ''
        else:
            finish_usage(report.plan_usage, False)
            report.status = 'FAILED'
            report.error_message = 'La consulta excedió el tiempo de espera. Inténtalo nuevamente.'
        report.completed_at = now
        report.save(update_fields=['status', 'error_message', 'completed_at'])


@transaction.atomic
def plan_summary(plan, now=None):
    Establishment.objects.select_for_update().get(pk=plan.establishment_id)
    plan.refresh_from_db()
    now = now or timezone.now()
    _recover_china_reports(plan, now)
    for usage in PlanUsage.objects.filter(
        establishment=plan.establishment, status='DISPATCHED', operation='print',
        created_at__lt=now - timedelta(hours=1),
    ):
        finish_usage(usage, True, completed_at=usage.created_at + timedelta(hours=1))
    plan.refresh_from_db()
    PlanUsage.objects.filter(
        establishment=plan.establishment,
        status='RESERVED',
        operation__in=['batch_pdf', 'print'],
        created_at__lt=now - timedelta(hours=1),
    ).update(status='CANCELLED')
    _expire_pro(plan, now)
    limit = {'FREE': 2, 'STARTER': 150, 'PRO': None}[plan.plan]
    used = _active_usages(plan, now).count()
    return {
        'plan': plan.plan,
        'limit': limit,
        'used': used,
        'remaining': max(limit - used, 0) if limit is not None else None,
        'expires_at': plan.activated_at + timedelta(days=30) if plan.plan == 'PRO' else None,
    }


@transaction.atomic
def assign_plan(establishment, plan_name):
    if plan_name not in dict(EstablishmentPlan.PLAN_CHOICES):
        raise ValueError('Plan inválido.')
    Establishment.objects.select_for_update().get(pk=establishment.pk)
    now = timezone.now()
    PlanUsage.objects.filter(establishment=establishment, status__in=['RESERVED', 'DISPATCHED']).update(status='CANCELLED')
    plan, _ = EstablishmentPlan.objects.update_or_create(
        establishment=establishment,
        defaults={
            'plan': plan_name,
            'activated_at': now,
            'free_reset_at': None,
            'alert_message': '',
        },
    )
    return plan


@transaction.atomic
def reserve_usage(user, operation):
    if _is_superadmin(user):
        return None
    establishment = establishment_for_user(user)
    if not establishment:
        raise PlanUsageError('Tu usuario no tiene un establecimiento asignado.')
    establishment = Establishment.objects.select_for_update().get(pk=establishment.pk)
    if not establishment.is_active or establishment.subscription_status == 'SUSPENDED':
        raise PlanUsageError('El establecimiento está suspendido o inactivo.')
    plan = EstablishmentPlan.objects.filter(establishment=establishment).first()
    if not plan:
        raise PlanUsageError('El establecimiento aún no tiene un plan asignado. Contacta al administrador.')
    now = timezone.now()
    summary = plan_summary(plan, now)
    if summary['remaining'] == 0:
        raise PlanUsageError('No quedan usos disponibles en tu plan. Contacta al administrador o espera la renovación de Free.')
    return PlanUsage.objects.create(
        establishment=establishment,
        user=user,
        plan=plan.plan,
        activation=plan.activated_at,
        operation=operation,
    )


@transaction.atomic
def finish_usage(usage, succeeded, completed_at=None):
    if usage is None:
        return True
    Establishment.objects.select_for_update().get(pk=usage.establishment_id)
    usage = PlanUsage.objects.select_for_update().get(pk=usage.pk)
    if usage.status not in ('RESERVED', 'DISPATCHED'):
        return usage.status == ('COMPLETED' if succeeded else 'CANCELLED')
    if usage.operation == 'batch_pdf' and usage.created_at < timezone.now() - timedelta(hours=1):
        usage.status = 'CANCELLED'
        usage.save(update_fields=['status'])
        return not succeeded
    usage.status = 'COMPLETED' if succeeded else 'CANCELLED'
    usage.completed_at = (completed_at or timezone.now()) if succeeded else None
    usage.save(update_fields=['status', 'completed_at'])
    if succeeded and usage.plan == 'STARTER':
        plan = EstablishmentPlan.objects.get(establishment_id=usage.establishment_id)
        if plan.plan == 'STARTER' and plan.activated_at == usage.activation:
            completed = PlanUsage.objects.filter(
                establishment=plan.establishment, plan='STARTER',
                activation=plan.activated_at, status='COMPLETED',
            ).count()
            if completed >= 150:
                plan.plan = 'FREE'
                plan.activated_at = timezone.now()
                plan.free_reset_at = None
                plan.alert_message = 'Agotaste los 150 usos de Starter y ahora tienes el plan Free.'
                plan.save(update_fields=['plan', 'activated_at', 'free_reset_at', 'alert_message', 'updated_at'])
    return True


@transaction.atomic
def reset_free(establishment):
    Establishment.objects.select_for_update().get(pk=establishment.pk)
    plan = EstablishmentPlan.objects.get(establishment=establishment)
    _expire_pro(plan, timezone.now())
    if plan.plan != 'FREE':
        raise PlanUsageError('Solo puedes reiniciar usos del plan Free.')
    now = timezone.now()
    _active_usages(plan, now).filter(status__in=['RESERVED', 'DISPATCHED']).update(status='CANCELLED')
    plan.free_reset_at = now
    plan.save(update_fields=['free_reset_at', 'updated_at'])
