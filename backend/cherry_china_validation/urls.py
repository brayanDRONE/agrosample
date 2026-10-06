from django.urls import path

from .views import (
    account_quota,
    admin_user_quota,
    admin_user_quotas,
    download_report,
    report_status,
    validate_cherry_china,
)


urlpatterns = [
    path('account/', account_quota, name='cherry-china-account'),
    path('admin/users/', admin_user_quotas, name='cherry-china-admin-user-quotas'),
    path('admin/users/<int:user_id>/', admin_user_quota, name='cherry-china-admin-user-quota'),
    path('validate/', validate_cherry_china, name='cherry-china-validate'),
    path('reports/<int:report_id>/status/', report_status, name='cherry-china-report-status'),
    path('reports/<int:report_id>/pdf/', download_report, name='cherry-china-report-pdf'),
]