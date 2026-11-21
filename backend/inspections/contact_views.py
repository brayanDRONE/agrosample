import json
import logging
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView


logger = logging.getLogger(__name__)

RESEND_ERROR_TYPES = {
    'invalid_permission', 'restricted_api_key', 'suspended_api_key', 'validation_error',
    'missing_api_key', 'rate_limit_exceeded', 'application_error', 'service_unavailable',
}


def _resend_error_details(error):
    try:
        body = json.loads(error.read(16384))
    except (ValueError, UnicodeDecodeError):
        return 'unrecognized_response', 'unknown'
    if not isinstance(body, dict):
        return 'unrecognized_response', 'unknown'
    error_type = body.get('name')
    if not isinstance(error_type, str) or error_type not in RESEND_ERROR_TYPES:
        error_type = 'unknown'
    message = str(body.get('message', '')).lower()
    reason = 'unknown'
    if 'only send testing emails' in message:
        reason = 'test_sender_restriction'
    elif 'domain' in message and 'not verified' in message:
        reason = 'domain_not_verified'
    elif 'api key' in message and 'not active' in message:
        reason = 'api_key_inactive'
    elif 'api key' in message and 'suspended' in message:
        reason = 'api_key_suspended'
    elif 'missing required scopes' in message:
        reason = 'missing_scopes'
    return error_type, reason


class ContactSubmissionSerializer(serializers.Serializer):
    nombre = serializers.CharField(max_length=100)
    empresa = serializers.CharField(max_length=120)
    email = serializers.EmailField(max_length=254)
    telefono = serializers.CharField(max_length=40, required=False, allow_blank=True)
    interes = serializers.ChoiceField(choices=[
        'Consulta general',
        'Free',
        'Starter',
        'Pro',
        'Pro mensual',
        'Pro semestral',
        'Pro anual',
        'Servicios de implementación',
    ])
    mensaje = serializers.CharField(max_length=5000)


class ContactSubmissionThrottle(AnonRateThrottle):
    rate = '5/hour'


class ContactSubmissionView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ContactSubmissionThrottle]

    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not all((
            settings.RESEND_API_KEY,
            settings.RESEND_FROM_EMAIL,
            settings.CONTACT_RECIPIENT_EMAIL,
        )):
            logger.error('Contact email is not configured; missing Resend environment variables.')
            return Response(
                {'message': 'El formulario no está disponible por el momento. Inténtalo más tarde.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        contact = serializer.validated_data
        message = '\n'.join((
            f"Nombre: {contact['nombre']}",
            f"Empresa: {contact['empresa']}",
            f"Correo: {contact['email']}",
            f"Teléfono: {contact.get('telefono') or 'No indicado'}",
            f"Interés: {contact['interes']}",
            '',
            contact['mensaje'],
        ))
        payload = {
            'from': settings.RESEND_FROM_EMAIL,
            'to': [settings.CONTACT_RECIPIENT_EMAIL],
            'reply_to': contact['email'],
            'subject': f"Contacto AgroSample.cl - {contact['interes']}",
            'text': message,
        }
        resend_request = Request(
            'https://api.resend.com/emails',
            data=json.dumps(payload).encode('utf-8'),
            headers={
                'Authorization': f'Bearer {settings.RESEND_API_KEY}',
                'Content-Type': 'application/json',
                'User-Agent': 'AgroSample/1.0',
            },
            method='POST',
        )

        try:
            with urlopen(resend_request, timeout=10) as response:
                if not 200 <= response.status < 300:
                    logger.error('Resend returned an unexpected status: %s', response.status)
                    return self._send_failed_response()
        except HTTPError as error:
            error_type, reason = _resend_error_details(error)
            logger.warning(
                'Resend rejected a contact email with status %s, type %s, reason %s.',
                error.code, error_type, reason,
            )
            return self._send_failed_response()
        except (URLError, TimeoutError):
            logger.exception('Could not reach Resend to send a contact email.')
            return self._send_failed_response()

        return Response(
            {'message': 'Tu consulta se envió correctamente.'},
            status=status.HTTP_202_ACCEPTED,
        )

    @staticmethod
    def _send_failed_response():
        return Response(
            {'message': 'No pudimos enviar tu consulta. Inténtalo nuevamente más tarde.'},
            status=status.HTTP_502_BAD_GATEWAY,
        )
