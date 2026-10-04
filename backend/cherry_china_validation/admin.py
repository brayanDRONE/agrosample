from django.contrib import admin

from .models import CherryChinaPlan, CherryChinaReport


@admin.register(CherryChinaPlan)
class CherryChinaPlanAdmin(admin.ModelAdmin):
    list_display = ['user', 'paid_until', 'updated_at']
    search_fields = ['user__username', 'user__email']
    list_filter = ['paid_until']


@admin.register(CherryChinaReport)
class CherryChinaReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'csg', 'csp', 'status', 'created_at', 'completed_at']
    search_fields = ['user__username', 'csg', 'csp']
    list_filter = ['status', 'created_at']
    readonly_fields = ['created_at', 'completed_at', 'results', 'sources', 'pdf_file']