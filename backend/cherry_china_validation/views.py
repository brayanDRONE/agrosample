import re
from io import BytesIO

from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import CherryChinaReport
from .pdf import build_validation_pdf
from .quota import ReportQuotaExceeded, get_account_quota, reserve_report
CODE_PATTERN = re.compile(r'^\d{3,12}$')


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_quota(request):
    return Response({'success': True, 'quota': get_account_quota(request.user)})


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
        return Response(
            {
                'success': False,
                'code': 'FREE_QUOTA_EXCEEDED',
                'message': 'Agotaste los 5 informes gratuitos de este mes.',
                'quota': get_account_quota(request.user),
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