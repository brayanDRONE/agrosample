from django.db import transaction

from inspections.models import EstablishmentPlan
from inspections.plan_usage import _is_superadmin, establishment_for_user, plan_summary, reserve_usage
from .models import CherryChinaReport


def get_account_quota(user):
    if _is_superadmin(user):
        return {'plan': 'ADMIN', 'unlimited': True, 'limit': None, 'used': 0, 'remaining': None}
    establishment = establishment_for_user(user)
    if not establishment:
        return {'plan': 'UNASSIGNED', 'unlimited': False, 'limit': 0, 'used': 0, 'remaining': 0}
    plan = EstablishmentPlan.objects.filter(establishment=establishment).first()
    if not plan:
        return {'plan': 'UNASSIGNED', 'unlimited': False, 'limit': 0, 'used': 0, 'remaining': 0}
    summary = plan_summary(plan)
    return {**summary, 'unlimited': summary['limit'] is None}


@transaction.atomic
def reserve_report(user, csg, csp, csgs=None, csps=None):
    usage = reserve_usage(user, 'china')
    return CherryChinaReport.objects.create(
        user=user,
        plan_usage=usage,
        csg=csg,
        csgs=csgs or ([csg] if csg else []),
        csp=csp,
        csps=csps or ([csp] if csp else []),
        status='QUEUED',
    )
