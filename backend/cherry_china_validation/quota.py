from django.db import transaction
from django.utils import timezone

from .models import CherryChinaPlan, CherryChinaReport


FREE_REPORT_LIMIT = 5
COUNTED_STATUSES = ['QUEUED', 'PROCESSING', 'COMPLETED']


class ReportQuotaExceeded(Exception):
    pass


def _month_usage(user):
    today = timezone.now().date()
    return CherryChinaReport.objects.filter(
        user=user,
        created_at__year=today.year,
        created_at__month=today.month,
        status__in=COUNTED_STATUSES,
    ).count()


def get_account_quota(user):
    plan, _ = CherryChinaPlan.objects.get_or_create(user=user)
    unlimited = plan.has_unlimited_usage()
    used = _month_usage(user)
    return {
        'plan': 'PAID' if unlimited else 'FREE',
        'unlimited': unlimited,
        'limit': None if unlimited else FREE_REPORT_LIMIT,
        'used': used,
        'remaining': None if unlimited else max(FREE_REPORT_LIMIT - used, 0),
    }


@transaction.atomic
def reserve_report(user, csg, csp, csgs=None, csps=None):
    CherryChinaPlan.objects.get_or_create(user=user)
    plan = CherryChinaPlan.objects.select_for_update().get(user=user)
    used = _month_usage(user)
    if not plan.has_unlimited_usage() and used >= FREE_REPORT_LIMIT:
        raise ReportQuotaExceeded
    return CherryChinaReport.objects.create(
        user=user,
        csg=csg,
        csgs=csgs or ([csg] if csg else []),
        csp=csp,
        csps=csps or ([csp] if csp else []),
        status='QUEUED',
    )