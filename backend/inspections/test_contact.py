import json
from io import BytesIO
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings
from rest_framework.test import APIClient


@override_settings(
    RESEND_API_KEY='test-resend-key',
    RESEND_FROM_EMAIL='AgroSample <contacto@example.com>',
    CONTACT_RECIPIENT_EMAIL='inbox@example.com',
)
class ContactSubmissionTests(SimpleTestCase):
    def setUp(self):
        cache.clear()
        self.client = APIClient()
        self.payload = {
            'nombre': 'Ana Pérez',
            'empresa': 'Packing de prueba',
            'email': 'ana@example.com',
            'telefono': '',
            'interes': 'Pro semestral',
            'mensaje': 'Quiero información sobre el plan.',
        }

    @patch('inspections.contact_views.urlopen')
    def test_sends_contact_email_through_resend_without_authentication(self, urlopen):
        response_mock = MagicMock()
        response_mock.__enter__.return_value.status = 200
        urlopen.return_value = response_mock

        response = self.client.post('/api/contact/', self.payload, format='json')

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['message'], 'Tu consulta se envió correctamente.')
        resend_request = urlopen.call_args.args[0]
        self.assertEqual(resend_request.full_url, 'https://api.resend.com/emails')
        self.assertEqual(resend_request.get_header('Authorization'), 'Bearer test-resend-key')
        self.assertEqual(resend_request.get_header('User-agent'), 'AgroSample/1.0')
        resend_payload = json.loads(resend_request.data)
        self.assertEqual(resend_payload['to'], ['inbox@example.com'])
        self.assertEqual(resend_payload['reply_to'], 'ana@example.com')
        self.assertIn('Pro semestral', resend_payload['text'])
        urlopen.assert_called_once_with(resend_request, timeout=10)

    @patch('inspections.contact_views.urlopen')
    def test_rejects_invalid_contact_data_without_sending_email(self, urlopen):
        self.payload.update({'email': 'not-an-email', 'interes': 'Unknown plan'})

        response = self.client.post('/api/contact/', self.payload, format='json')

        self.assertEqual(response.status_code, 400)
        urlopen.assert_not_called()

    @override_settings(RESEND_API_KEY='')
    @patch('inspections.contact_views.urlopen')
    def test_returns_service_unavailable_when_email_is_not_configured(self, urlopen):
        response = self.client.post('/api/contact/', self.payload, format='json')

        self.assertEqual(response.status_code, 503)
        urlopen.assert_not_called()

    @patch('inspections.contact_views.urlopen')
    def test_reports_provider_failure_without_exposing_provider_details(self, urlopen):
        urlopen.side_effect = HTTPError(
            'https://api.resend.com/emails',
            401,
            'Unauthorized',
            hdrs=None,
            fp=BytesIO(b'provider details'),
        )

        with self.assertLogs('inspections.contact_views', level='WARNING') as logs:
            response = self.client.post('/api/contact/', self.payload, format='json')

        self.assertEqual(response.status_code, 502)
        self.assertIn('unrecognized_response', logs.output[0])
        self.assertEqual(
            response.data['message'],
            'No pudimos enviar tu consulta. Inténtalo nuevamente más tarde.',
        )

    @patch('inspections.contact_views.urlopen')
    def test_logs_only_safe_provider_error_classification(self, urlopen):
        urlopen.side_effect = HTTPError(
            'https://api.resend.com/emails',
            403,
            'Forbidden',
            hdrs=None,
            fp=BytesIO(json.dumps({
                'name': 'validation_error',
                'message': 'The private.example.com domain is not verified.',
            }).encode()),
        )
        with self.assertLogs('inspections.contact_views', level='WARNING') as logs:
            response = self.client.post('/api/contact/', self.payload, format='json')

        self.assertEqual(response.status_code, 502)
        self.assertIn('validation_error', logs.output[0])
        self.assertIn('domain_not_verified', logs.output[0])
        self.assertNotIn('private.example.com', logs.output[0])
