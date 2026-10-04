from django.urls import path

from .views import account_quota, download_report, report_status, validate_cherry_china


urlpatterns = [
    path('account/', account_quota, name='cherry-china-account'),
    path('validate/', validate_cherry_china, name='cherry-china-validate'),
    path('reports/<int:report_id>/status/', report_status, name='cherry-china-report-status'),
    path('reports/<int:report_id>/pdf/', download_report, name='cherry-china-report-pdf'),
]