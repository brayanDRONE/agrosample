import re
from io import BytesIO

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from django.contrib.auth.models import User
from inspections.views_admin import IsSuperAdmin

from .models import CherryChinaPlan, CherryChinaReport
from .pdf import build_validation_pdf
from .quota import ReportQuotaExceeded, get_account_quota, reserve_report
CODE_PATTERN = re.compile(r'^\d{3,12}$')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_quota(request):
    return Response({'success': True, 'quota': get_account_quota(request.user)})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def admin_user_quotas(request):
    users = User.objects.exclude(
        profile__role='SUPERADMIN',
    ).exclude(
        is_superuser=True,
    ).order_by('username')
    return Response({
        'success': True,
        'users': [
            {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'quota': get_account_quota(user),
            }
            for user in users
        ],
    })


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def admin_user_quota(request, user_id):
    try:
        user = User.objects.exclude(
            profile__role='SUPERADMIN',
        ).exclude(
            is_superuser=True,
        ).get(pk=user_id)
    except User.DoesNotExist:
        return Response(
            {'success': False, 'message': 'No se encontró el usuario.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    unlimited = request.data.get('unlimited')
    if not isinstance(unlimited, bool):
        return Response(
            {'success': False, 'message': 'Indique si el acceso será ilimitado.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if unlimited:
        monthly_limit = None
    else:
        monthly_limit = request.data.get('monthly_limit')
        if isinstance(monthly_limit, bool) or not isinstance(monthly_limit, int) or monthly_limit < 0:
            return Response(
                {'success': False, 'message': 'El límite mensual debe ser un número entero igual o mayor que cero.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
    plan, _ = CherryChinaPlan.objects.get_or_create(user=user)
    plan.unlimited = unlimited
    plan.monthly_report_limit = monthly_limit
    plan.save(update_fields=['unlimited', 'monthly_report_limit', 'updated_at'])

    return Response({
        'success': True,
        'user': {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'quota': get_account_quota(user),
        },
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_cherry_china(request):
    raw_csgs = request.data.get('csgs')
    if raw_csgs is None:
        raw_csgs = [request.data.get('csg', '')]
    elif isinstance(raw_csgs, str):
        raw_csgs = re.split(r'[\s,;]+', raw_csgs)
    if not isinstance(raw_csgs, (list, tuple)):
        return Response(
            {'success': False, 'message': 'Los códigos CSG deben enviarse como lista o texto separado por coma.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    csgs = list(dict.fromkeys(str(code or '').strip() for code in raw_csgs if str(code or '').strip()))
    raw_csps = request.data.get('csps')
    if raw_csps is None:
        raw_csps = [request.data.get('csp', '')]
    elif isinstance(raw_csps, str):
        raw_csps = re.split(r'[\s,;]+', raw_csps)
    if not isinstance(raw_csps, (list, tuple)):
        return Response(
            {'success': False, 'message': 'Los códigos CSP deben enviarse como lista o texto separado por coma.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    csps = list(dict.fromkeys(str(code or '').strip() for code in raw_csps if str(code or '').strip()))
    csp = csps[0] if csps else ''
    if not csgs and not csps:
        return Response(
            {'success': False, 'message': 'Ingrese un código CSG o CSP.'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if any(not CODE_PATTERN.fullmatch(code) for code in csgs + csps):
        return Response(
            {'success': False, 'message': 'Los códigos CSG y CSP deben contener entre 3 y 12 dígitos.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        csg = csgs[0] if csgs else ''
        report = reserve_report(request.user, csg, csp, csgs=csgs, csps=csps)
    except ReportQuotaExceeded:
        quota = get_account_quota(request.user)
        return Response(
            {
                'success': False,
                'code': 'FREE_QUOTA_EXCEEDED',
                'message': (
                    f'Alcanzaste el límite de {quota["limit"]} informes de este mes.'
                    if quota['plan'] == 'CUSTOM'
                    else 'Agotaste los 5 informes gratuitos de este mes.'
                ),
                'quota': quota,
            },
            status=status.HTTP_429_TOO_MANY_REQUESTS,
        )

    return Response({
        'success': True,
        'report_id': report.pk,
        'status': report.status,
        'quota': get_account_quota(request.user),
        'status_url': request.build_absolute_uri(
            f'/api/cherry-china/reports/{report.pk}/status/'
        ),
    }, status=status.HTTP_202_ACCEPTED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def report_status(request, report_id):
    report = get_object_or_404(CherryChinaReport, pk=report_id, user=request.user)
    response_data = {
        'success': True,
        'report_id': report.pk,
        'status': report.status,
        'quota': get_account_quota(request.user),
    }
    if report.status == 'COMPLETED':
        response_data.update({
            'results': report.results,
            'sources': report.sources,
            'pdf_url': request.build_absolute_uri(f'/api/cherry-china/reports/{report.pk}/pdf/'),
        })
    elif report.status == 'FAILED':
        response_data['message'] = report.error_message or 'No se pudo generar el informe.'
    return Response(response_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_report(request, report_id):
    report = get_object_or_404(CherryChinaReport, pk=report_id, user=request.user)
    if report.status != 'COMPLETED':
        return Response(
            {'success': False, 'message': 'El informe PDF no está disponible.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    if report.pdf_data:
        pdf_stream = BytesIO(bytes(report.pdf_data))
    elif report.pdf_file:
        try:
            pdf_stream = report.pdf_file.open('rb')
        except (FileNotFoundError, OSError):
            pdf_stream = None
    else:
        pdf_stream = None

    if pdf_stream is None and report.results and report.sources:
        pdf_bytes = build_validation_pdf(report, report.results, report.sources)
        report.pdf_data = pdf_bytes
        report.save(update_fields=['pdf_data'])
        pdf_stream = BytesIO(pdf_bytes)

    if pdf_stream is None:
        return Response(
            {'success': False, 'message': 'El informe PDF no está disponible.'},
            status=status.HTTP_404_NOT_FOUND,
        )

    return FileResponse(
        pdf_stream,
        content_type='application/pdf',
        as_attachment=True,
        filename=f'validacion_cereza_china_{report.pk}.pdf',
    )