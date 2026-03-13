"""
Tests para el sistema de inspecciones.
"""
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from .models import Establishment, Inspection, SamplingResult
from .utils import calcular_muestreo, generar_cajas_aleatorias, validar_datos_inspeccion
import json


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
        """Verifica que detecta suscripciones expiradas"""
        self.establishment.subscription_expiry = timezone.now().date() - timedelta(days=1)
        self.establishment.save()
        self.assertFalse(self.establishment.has_active_subscription())
    
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
