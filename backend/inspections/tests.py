"""
Tests para el sistema de inspecciones.
"""
from django.test import SimpleTestCase, TestCase
from django.utils import timezone
from datetime import timedelta
from .models import Establishment, Inspection, SamplingResult
from .utils import calcular_muestreo, generar_cajas_aleatorias, validar_datos_inspeccion
from .dispatch_flatfile import build_dispatch_flat_file
import json
import os
import subprocess
import sys
from django.contrib.auth.models import User
from django.core.management import call_command
from django.core.management.base import CommandError
from rest_framework.test import APIClient
from .models import UserProfile


class DeploymentOriginsTest(SimpleTestCase):
    def settings_for(self, debug, **overrides):
        env = os.environ.copy()
        for name in (
            'CORS_ALLOWED_ORIGINS', 'CSRF_TRUSTED_ORIGINS', 'FRONTEND_URL',
            'RENDER', 'RENDER_EXTERNAL_HOSTNAME', 'RAILWAY_ENVIRONMENT',
            'DATABASE_URL', 'SECRET_KEY',
        ):
            env.pop(name, None)
        env.update({
            'DEBUG': str(debug),
            'SECRET_KEY': 'deployment-check-key-with-no-real-credentials-123456789',
            'DATABASE_URL': 'postgresql://test:test@localhost:5432/test',
            **overrides,
        })
        result = subprocess.run(
            [sys.executable, '-c', (
                'import json; import config.settings as s; '
                'print(json.dumps([s.CORS_ALLOWED_ORIGINS, s.CSRF_TRUSTED_ORIGINS]))'
            )],
            cwd=os.path.dirname(os.path.dirname(__file__)),
            env=env, capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)

    def test_loopback_origins_are_not_implicitly_trusted_in_production(self):
        cors, csrf = self.settings_for(False)
        self.assertFalse(any('localhost' in origin or '127.0.0.1' in origin for origin in cors + csrf))
        cors, csrf = self.settings_for(True)
        self.assertIn('http://localhost:5173', cors)
        self.assertIn('http://localhost:5173', csrf)

    def test_explicit_production_frontend_origins_are_preserved(self):
        origin = 'https://test-frontend.example'
        cors, csrf = self.settings_for(
            False, CORS_ALLOWED_ORIGINS=origin, CSRF_TRUSTED_ORIGINS=origin,
        )
        self.assertIn(origin, cors)
        self.assertIn(origin, csrf)


class InspectionAccessTest(TestCase):
    def setUp(self):
        self.first = Establishment.objects.create(planta_fruticola='Primero', license_key='access-1')
        self.second = Establishment.objects.create(planta_fruticola='Segundo', license_key='access-2')
        self.user = User.objects.create_user(username='access-user')
        UserProfile.objects.create(user=self.user, establishment=self.first)
        self.admin = User.objects.create_superuser(username='access-admin', password='test-password')
        UserProfile.objects.create(user=self.admin, role='SUPERADMIN')
        self.client = APIClient()
        self.own = self.inspection(self.first, 'A')
        self.other = self.inspection(self.second, 'B')
        self.orphan = self.inspection(None, 'C')
        self.other_result = SamplingResult.objects.create(
            inspection=self.other, tamano_muestra=1, cajas_seleccionadas='[1]',
        )

    def inspection(self, establishment, lot):
        return Inspection.objects.create(
            establishment=establishment, exportador='Test', inspector_sag='Test',
            contraparte_sag='Test', especie='Uva', numero_lote=lot, tamano_lote=10,
            tipo_despacho='Test', cantidad_pallets=1,
        )

    def test_anonymous_access_is_denied(self):
        for url in [
            '/api/inspections/', '/api/sampling-results/', '/api/establishments/',
            '/api/themes/', f'/api/muestreo/diagrama-pallets/{self.own.pk}/',
        ]:
            self.assertEqual(self.client.get(url).status_code, 401, url)
        self.assertEqual(self.client.post('/api/muestreo/generar/', {}, format='json').status_code, 401)
        self.assertEqual(self.client.post('/api/dispatch-flatfile/generate/', {}, format='json').status_code, 401)
        self.assertEqual(self.client.get('/media/sdp_validation/old.pdf').status_code, 404)
        self.assertEqual(self.client.get('/media/cherry_china/reports/old.pdf').status_code, 404)

    def test_establishment_isolation_and_legacy_admin_access(self):
        self.client.force_authenticate(self.user)
        response = self.client.get('/api/inspections/')
        self.assertEqual([item['id'] for item in response.data], [self.own.pk])
        self.assertEqual(self.client.get(f'/api/inspections/{self.other.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/inspections/{self.orphan.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/sampling-results/{self.other_result.pk}/').status_code, 404)
        self.assertEqual(self.client.get(f'/api/muestreo/diagrama-pallets/{self.other.pk}/').status_code, 404)
        self.assertEqual(self.client.post(
            f'/api/muestreo/configurar-pallets/{self.other.pk}/', {'configurations': []}, format='json',
        ).status_code, 404)
        self.assertEqual(self.client.patch(
            f'/api/inspections/{self.own.pk}/', {'establishment': self.second.pk}, format='json',
        ).status_code, 400)
        self.client.force_authenticate(self.admin)
        self.assertEqual(self.client.get(f'/api/inspections/{self.orphan.pk}/').status_code, 200)

    def test_new_sampling_belongs_to_authenticated_establishment(self):
        self.client.force_authenticate(self.user)
        response = self.client.post(
            '/api/muestreo/generar/', {'numero_lote': 'NUEVO', 'cantidad_pallets': 1}, format='json',
        )
        self.assertEqual(response.status_code, 201)
        inspection = Inspection.objects.get(pk=response.data['data']['inspection']['id'])
        self.assertEqual(inspection.establishment, self.first)
        self.first.subscription_status = 'SUSPENDED'
        self.first.save(update_fields=['subscription_status'])
        self.assertEqual(self.client.get('/api/inspections/').status_code, 403)

    def test_create_cannot_assign_another_establishment(self):
        self.client.force_authenticate(self.user)
        payload = {
            'establishment': self.second.pk, 'exportador': 'Test', 'inspector_sag': 'Test',
            'contraparte_sag': 'Test', 'especie': 'Uva', 'numero_lote': 'NEW',
            'tamano_lote': 10, 'tipo_despacho': 'Test', 'cantidad_pallets': 1,
        }
        self.assertEqual(self.client.post('/api/inspections/', payload, format='json').status_code, 400)
        payload.pop('establishment')
        response = self.client.post('/api/inspections/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['establishment'], self.first.pk)

    def test_create_admin_requires_existing_superuser(self):
        with self.assertRaises(CommandError):
            call_command('create_admin', self.user.username)
        call_command('create_admin', self.admin.username)
        self.assertEqual(self.admin.profile.role, 'SUPERADMIN')

    def test_admin_can_change_establishment_password_and_revoke_old_tokens(self):
        self.user.set_password('Initial-safe-pass-842')
        self.user.save()
        self.first.admin_user = self.user
        self.first.save(update_fields=['admin_user'])
        login = self.client.post('/api/auth/login/', {
            'username': self.user.username, 'password': 'Initial-safe-pass-842',
        }, format='json')
        old_access = login.data['access']
        old_refresh = login.data['refresh']
        self.client.force_authenticate(self.admin)
        url = f'/api/admin/establishments/{self.first.pk}/'
        weak = self.client.patch(url, {'admin_password': '123'}, format='json')
        self.assertEqual(weak.status_code, 400)
        changed = self.client.patch(url, {'admin_password': 'New-safe-pass-974'}, format='json')
        self.assertEqual(changed.status_code, 200)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password('New-safe-pass-974'))
        self.client.force_authenticate(None)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {old_access}')
        self.assertEqual(self.client.get('/api/inspections/').status_code, 401)
        self.client.credentials()
        refresh = self.client.post('/api/auth/refresh/', {'refresh': old_refresh}, format='json')
        self.assertIn(refresh.status_code, (200, 401))
        if refresh.status_code == 200:
            self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.data['access']}")
            self.assertEqual(self.client.get('/api/inspections/').status_code, 401)

    def test_new_establishment_rejects_weak_credentials(self):
        self.client.force_authenticate(self.admin)
        payload = {
            'planta_fruticola': 'Nueva',
            'admin_username': 'new-establishment-admin',
            'admin_password': '123',
        }
        response = self.client.post('/api/admin/establishments/', payload, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('admin_password', response.data)
        self.assertFalse(User.objects.filter(username=payload['admin_username']).exists())
        payload['admin_password'] = 'Strong-pass-9375'
        response = self.client.post('/api/admin/establishments/', payload, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertTrue(User.objects.get(username=payload['admin_username']).check_password(payload['admin_password']))


class EstablishmentModelTest(TestCase):
    """Tests para el modelo Establishment"""
    
    def setUp(self):
        self.establishment = Establishment.objects.create(
            planta_fruticola='Test Establishment',
            is_active=True,
            subscription_status='ACTIVE',
            subscription_expiry=timezone.now().date() + timedelta(days=30),
            license_key='TEST-KEY-001'
        )
    
    def test_establishment_creation(self):
        """Verifica que un establecimiento se crea correctamente"""
        self.assertEqual(self.establishment.planta_fruticola, 'Test Establishment')
        self.assertTrue(self.establishment.is_active)
        self.assertEqual(self.establishment.subscription_status, 'ACTIVE')
    
    def test_has_active_subscription(self):
        """Verifica que la validación de suscripción funciona"""
        self.assertTrue(self.establishment.has_active_subscription())
    
    def test_expired_subscription(self):
        """La fecha histórica vencida ya no bloquea el acceso."""
        self.establishment.subscription_expiry = timezone.now().date() - timedelta(days=1)
        self.establishment.save()
        self.assertTrue(self.establishment.has_active_subscription())
    
    def test_suspended_subscription(self):
        """Verifica que detecta suscripciones suspendidas"""
        self.establishment.subscription_status = 'SUSPENDED'
        self.establishment.save()
        self.assertFalse(self.establishment.has_active_subscription())


class SamplingUtilsTest(TestCase):
    """Tests para las utilidades de muestreo"""
    
    def test_calcular_muestreo_basico(self):
        """Verifica el cálculo básico de muestreo al 2%"""
        resultado = calcular_muestreo(100, porcentaje=2.0)
        self.assertEqual(resultado['tamano_lote'], 100)
        self.assertEqual(resultado['tamano_muestra'], 2)
        self.assertEqual(len(resultado['cajas_seleccionadas']), 2)
    
    def test_calcular_muestreo_redondeo(self):
        """Verifica que redondea hacia arriba (ceil)"""
        resultado = calcular_muestreo(2332, porcentaje=2.0)
        # 2332 * 0.02 = 46.64, redondeado = 47
        self.assertEqual(resultado['tamano_muestra'], 47)
        self.assertEqual(len(resultado['cajas_seleccionadas']), 47)
    
    def test_cajas_unicas(self):
        """Verifica que las cajas generadas son únicas"""
        resultado = calcular_muestreo(1000, porcentaje=5.0)
        cajas = resultado['cajas_seleccionadas']
        self.assertEqual(len(cajas), len(set(cajas)))  # Sin duplicados
    
    def test_cajas_ordenadas(self):
        """Verifica que las cajas están ordenadas"""
        resultado = calcular_muestreo(1000, porcentaje=5.0)
        cajas = resultado['cajas_seleccionadas']
        self.assertEqual(cajas, sorted(cajas))
    
    def test_cajas_en_rango(self):
        """Verifica que las cajas están en el rango correcto"""
        tamano_lote = 500
        resultado = calcular_muestreo(tamano_lote, porcentaje=4.0)
        cajas = resultado['cajas_seleccionadas']
        
        for caja in cajas:
            self.assertGreaterEqual(caja, 1)
            self.assertLessEqual(caja, tamano_lote)
    
    def test_error_lote_negativo(self):
        """Verifica que rechaza tamaños de lote inválidos"""
        with self.assertRaises(ValueError):
            calcular_muestreo(-10, porcentaje=2.0)
    
    def test_error_porcentaje_invalido(self):
        """Verifica que rechaza porcentajes inválidos"""
        with self.assertRaises(ValueError):
            calcular_muestreo(100, porcentaje=0)
        with self.assertRaises(ValueError):
            calcular_muestreo(100, porcentaje=150)


class InspectionModelTest(TestCase):
    """Tests para el modelo Inspection"""
    
    def setUp(self):
        self.establishment = Establishment.objects.create(
            planta_fruticola='Test Establishment',
            is_active=True,
            subscription_status='ACTIVE',
            subscription_expiry=timezone.now().date() + timedelta(days=30),
            license_key='TEST-KEY-002'
        )
    
    def test_inspection_creation(self):
        """Verifica que una inspección se crea correctamente"""
        inspection = Inspection.objects.create(
            exportador='Test Exporter',
            establishment=self.establishment,
            inspector_sag='Inspector Test',
            contraparte_sag='Contraparte Test',
            especie='Uva de Mesa',
            numero_lote='TEST-LOT-001',
            tamano_lote=1000,
            tipo_muestreo='NORMAL',
            tipo_despacho='Marítimo',
            cantidad_pallets=20
        )
        
        self.assertEqual(inspection.exportador, 'Test Exporter')
        self.assertEqual(inspection.tamano_lote, 1000)
        self.assertIsNotNone(inspection.fecha)
        self.assertIsNotNone(inspection.hora)


class DispatchFlatFileTest(TestCase):
    """Tests para la generación del archivo plano de despacho Multipuerto (42 campos)"""

    def test_build_dispatch_flat_file_multipuerto_42_fields(self):
        """Test building a Multipuerto flat file with 42 fields."""
        payload = {
            'codigo_exportadora': '90388',
            'nro_planilla': '1666',
            'codigo_puerto_embarque': '56',
            'codigo_puerto_destino': '107',
            'codigo_producto': '2624',
            'tipo_transporte': '5',
            'patente_camion': 'FTVC60',
            'patente_carro': '0064794',
            'fecha_despacho': '2026-05-29',
            'nro_pallet_ubicacion': '123',
            'cantidad_kg': '1968.0000',
            'codigo_especie': '4',
            'codigo_variedad': '4',
            'codigo_establecimiento': '1378',
            'numero_contenedor': 'HLBU970121-7',
            'codigo_tipo_envase': '1',
            'codigo_csg': '07,03,08',
            'cantidad_envases': '2',
            'total_kg_decimales': '10207,1',
            'ubicacion_sello': '1',
            'numero_sellos': '49',
            'tipo_produccion': '1',
            'transgenico': '1',
            'codigo_agencia_aduana': 'PTXT92',
            'tratado': '0',
            'codigo_establecimiento_2': '1378',
            'reservado': 'DELEGADO',
            'codigo_pais_destino': '23',
            'codigo_pais_puerto_destino': '120877',
            'codigo_exportadora_final': '90388',
        }

        filename, content = build_dispatch_flat_file(payload)

        self.assertTrue(filename.startswith('Multipuerto_1666_'))
        self.assertTrue(filename.endswith('.txt'))
        self.assertEqual(content.split(';'), [
            '90388', '1666', '56', '107', '2624', '5', 'FTVC60', '0064794',
            '2026-05-29', '123', '1968.0000', '4', '4', '1378', 'HLBU970121-7',
            '1', '07,03,08', '', '', '', '', '', '', '2', '12', '10207,1',
            '1', '', '49', '', '', '1', '1', 'PTXT92', '', '0', '', '1378',
            'DELEGADO', '23', '120877', '90388',
        ])

    def test_build_dispatch_flat_file_special_chars(self):
        """El separador y los saltos de línea no deben crear campos ni registros."""
        payload = {
            'nro_planilla': 'TEST123',
            'patente_camion': 'CERT;TEST\r\nPLACA',
            'codigo_csg': '07,03,08',
            'total_kg_decimales': '10207,1',
        }

        _, content = build_dispatch_flat_file(payload)
        fields = content.split(';')
        self.assertEqual(len(fields), 42)
        self.assertEqual(fields[6], 'CERTTEST  PLACA')
        self.assertEqual(fields[16], '07,03,08')
        self.assertEqual(fields[25], '10207,1')
        self.assertNotIn('\r', content)
        self.assertNotIn('\n', content)


class ValidationTest(TestCase):
    """Tests para las validaciones"""
    
    def test_validacion_datos_completos(self):
        """Verifica validación con datos completos"""
        data = {
            'exportador': 'Test',
            'establishment': 1,
            'inspector_sag': 'Inspector',
            'contraparte_sag': 'Contraparte',
            'especie': 'Uva',
            'numero_lote': 'LOT-001',
            'tamano_lote': 100,
            'tipo_muestreo': 'NORMAL',
            'tipo_despacho': 'Marítimo',
            'cantidad_pallets': 5
        }
        
        es_valido, errores = validar_datos_inspeccion(data)
        self.assertTrue(es_valido)
        self.assertEqual(len(errores), 0)
    
    def test_validacion_campos_faltantes(self):
        """Verifica validación con campos faltantes"""
        data = {
            'exportador': 'Test',
            # Faltan muchos campos
        }
        
        es_valido, errores = validar_datos_inspeccion(data)
        self.assertFalse(es_valido)
        self.assertGreater(len(errores), 0)
    
    def test_validacion_valores_negativos(self):
        """Verifica validación de valores negativos"""
        data = {
            'exportador': 'Test',
            'establishment': 1,
            'inspector_sag': 'Inspector',
            'contraparte_sag': 'Contraparte',
            'especie': 'Uva',
            'numero_lote': 'LOT-001',
            'tamano_lote': -100,  # Inválido
            'tipo_muestreo': 'NORMAL',
            'tipo_despacho': 'Marítimo',
            'cantidad_pallets': 5
        }
        
        es_valido, errores = validar_datos_inspeccion(data)
        self.assertFalse(es_valido)
