from io import BytesIO

from django.http import FileResponse
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Establishment, EstablishmentPlan, PlanBatchArtifact, PlanUsage
from .plan_usage import PlanUsageError, establishment_for_user, finish_usage, plan_summary, reserve_usage


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def account_plan(request):
    establishment = establishment_for_user(request.user)
    if not establishment:
        return Response({'message': 'Tu usuario no tiene un establecimiento asignado.'}, status=400)
    plan = EstablishmentPlan.objects.filter(establishment=establishment).first()
    return Response({'plan': plan_summary(plan) if plan else None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def acknowledge_plan_alert(request):
    establishment = establishment_for_user(request.user)
    if not establishment:
        return Response({'message': 'Tu usuario no tiene un establecimiento asignado.'}, status=400)
    message = request.data.get('message')
    if not isinstance(message, str) or not message:
        return Response({'message': 'Aviso no válido.'}, status=400)
    EstablishmentPlan.objects.filter(establishment=establishment, alert_message=message).update(alert_message='')
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reserve_client_operation(request):
    operation = request.data.get('operation')
    if operation not in ('print', 'diagram'):
        return Response({'message': 'Operación no válida.'}, status=status.HTTP_400_BAD_REQUEST)
    try:
        usage = reserve_usage(request.user, operation)
    except PlanUsageError as error:
        return Response({'message': str(error)}, status=status.HTTP_403_FORBIDDEN)
    return Response({'reservation_id': usage.pk if usage else None})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def dispatch_print(request, usage_id):
    with transaction.atomic():
        usage = get_object_or_404(PlanUsage, pk=usage_id, user=request.user, operation='print')
        establishment = Establishment.objects.select_for_update().get(pk=usage.establishment_id)
        usage = PlanUsage.objects.select_for_update().get(pk=usage.pk)
        if establishment_for_user(request.user) != establishment or not establishment.is_active or establishment.subscription_status == 'SUSPENDED':
            return Response({'message': 'El establecimiento está suspendido o no corresponde a esta reserva.'}, status=403)
        if usage.status == 'RESERVED':
            usage.status = 'DISPATCHED'
            usage.save(update_fields=['status'])
        elif usage.status != 'DISPATCHED':
            return Response({'message': 'Esta reserva ya fue cerrada.'}, status=409)
    return Response({'success': True})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def finish_client_operation(request, usage_id):
    usage = get_object_or_404(PlanUsage, pk=usage_id, user=request.user, operation__in=['print', 'diagram'])
    succeeded = request.data.get('succeeded')
    if not isinstance(succeeded, bool):
        return Response({'message': 'Indica si la operación fue exitosa.'}, status=400)
    if not finish_usage(usage, succeeded):
        return Response({'message': 'Esta reserva ya fue cerrada de otra forma.'}, status=409)
    return Response({'success': True})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def download_batch_pdf(request, artifact_id):
    artifact = get_object_or_404(PlanBatchArtifact, pk=artifact_id, user=request.user)
    if artifact.usage:
        establishment = establishment_for_user(request.user)
        if not establishment or establishment.pk != artifact.usage.establishment_id:
            return Response({'message': 'Este documento pertenece a otro establecimiento.'}, status=403)
        if not establishment.is_active or establishment.subscription_status == 'SUSPENDED':
            return Response({'message': 'El establecimiento está suspendido o inactivo.'}, status=403)
        if not finish_usage(artifact.usage, True):
            return Response({'message': 'La reserva de este documento fue cancelada. Genera la planilla nuevamente.'}, status=409)
    return FileResponse(BytesIO(bytes(artifact.data)), content_type='application/pdf', as_attachment=True, filename=artifact.filename)
