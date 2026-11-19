"""Comprobaciones de las tablas de muestreo SAG-USDA."""
import unittest

from inspections.utils import calcular_muestreo


class TablasMuestreoTests(unittest.TestCase):
    def test_tablas_por_especie(self):
        casos = {
            'Damasco': [
                (50, 50), (900, 900), (901, 63), (1500, 63), (1501, 90),
                (4000, 90), (5000, 94), (12000, 96), (18000, 98), (25000, 99),
            ],
            'Durazno': [
                (10, 10), (37, 37), (38, 37), (78, 37), (79, 38), (100, 39),
                (120, 40), (150, 41), (200, 43), (300, 45), (400, 46),
                (500, 47), (700, 47), (1000, 48), (2250, 48), (2251, 49),
                (5000, 49), (10000, 49), (50000, 49),
            ],
            'Manzana': [
                (10, 10), (30, 30), (31, 30), (100, 30), (2000, 30),
                (2001, 50), (5000, 50), (10000, 50), (10001, 100), (50000, 100),
            ],
            'Arándano': [
                (50, 2), (100, 2), (101, 2), (124, 2),
                (125, 3), (150, 3), (200, 4), (1000, 20),
            ],
        }
        for especie, valores in casos.items():
            for lote, esperado in valores:
                with self.subTest(especie=especie, lote=lote):
                    self.assertEqual(calcular_muestreo(lote, especie=especie)['tamano_muestra'], esperado)

    def test_ciruela_no_supera_49_unidades(self):
        for lote in [3000, 10000, 50000, 100000, 500000]:
            with self.subTest(lote=lote):
                self.assertLessEqual(calcular_muestreo(lote, especie='Ciruela')['tamano_muestra'], 49)


if __name__ == '__main__':
    unittest.main()
