from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone


class CherryChinaPlan(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cherry_china_plan',
    )
    paid_until = models.DateField(null=True, blank=True)
    monthly_report_limit = models.PositiveIntegerField(
        null=True,
        blank=True,
        validators=[MinValueValidator(0)],
    )
    unlimited = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Plan de Validación Cereza China'
        verbose_name_plural = 'Planes de Validación Cereza China'

    def has_unlimited_usage(self):
        if self.unlimited:
            return True
        return self.monthly_report_limit is None and bool(
            self.paid_until and self.paid_until >= timezone.now().date()
        )

    def __str__(self):
        plan_type = 'Pagado' if self.has_unlimited_usage() else 'Gratuito'
        return f'{self.user} - {plan_type}'


class CherryChinaReport(models.Model):
    STATUS_CHOICES = [
        ('QUEUED', 'En cola'),
        ('PROCESSING', 'En proceso'),
        ('COMPLETED', 'Completado'),
        ('FAILED', 'Fallido'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cherry_china_reports',
    )
    csg = models.CharField(max_length=30, blank=True)
    csgs = models.JSONField(default=list, blank=True)
    csp = models.CharField(max_length=30, blank=True)
    csps = models.JSONField(default=list, blank=True)
    status = models.CharField(max_length=12, choices=STATUS_CHOICES, default='PROCESSING')
    started_at = models.DateTimeField(null=True, blank=True)
    attempts = models.PositiveSmallIntegerField(default=0)
    results = models.JSONField(default=dict, blank=True)
    sources = models.JSONField(default=list, blank=True)
    pdf_file = models.FileField(upload_to='cherry_china/reports/', blank=True)
    pdf_data = models.BinaryField(blank=True, null=True, editable=False)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at', 'status']),
        ]
        verbose_name = 'Informe Cereza China'
        verbose_name_plural = 'Informes Cereza China'

    def __str__(self):
        csgs = ', '.join(self.csgs or []) or self.csg or '-'
        return f'Informe {self.id} · CSG {csgs} · CSP {self.csp or "-"}'