from datetime import timedelta
from io import BytesIO
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pdfplumber
from django.contrib.auth.models import User
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from inspections.models import UserProfile

from .models import CherryChinaPlan, CherryChinaReport
from .pdf import build_validation_pdf
from .quota import FREE_REPORT_LIMIT, ReportQuotaExceeded, get_account_quota, reserve_report
from .rules import summarize_campaign_rows, summarize_chinaport_rows, summarize_descolgados
from .sources import (
    _map_powerbi_row,
    map_descolgados_cells,
    parse_cherry_species,
    run_cherry_china_checks,
)
from .worker import claim_next_report, process_report


class CherryChinaQuotaTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='quota-test', password='test-password')

    def test_new_user_has_five_free_reports(self):
        quota = get_account_quota(self.user)
        self.assertEqual(quota['limit'], FREE_REPORT_LIMIT)
        self.assertEqual(quota['remaining'], FREE_REPORT_LIMIT)
        self.assertFalse(quota['unlimited'])

    def test_failed_reports_do_not_consume_monthly_quota(self):
        for _ in range(FREE_REPORT_LIMIT):
            CherryChinaReport.objects.create(user=self.user, status='FAILED')

        report = reserve_report(self.user, '176264', '')
        self.assertEqual(report.status, 'QUEUED')

    def test_completed_and_processing_reports_reserve_the_free_quota(self):
        for status in ['COMPLETED'] * FREE_REPORT_LIMIT:
            CherryChinaReport.objects.create(user=self.user, status=status)

        with self.assertRaises(ReportQuotaExceeded):
            reserve_report(self.user, '176264', '')

    def test_paid_plan_has_unlimited_usage(self):
        CherryChinaPlan.objects.create(
            user=self.user,
            paid_until=timezone.now().date() + timedelta(days=30),
        )
        for _ in range(FREE_REPORT_LIMIT + 2):
            CherryChinaReport.objects.create(user=self.user, status='COMPLETED')

        report = reserve_report(self.user, '176264', '')
        self.assertEqual(report.status, 'QUEUED')
        self.assertTrue(get_account_quota(self.user)['unlimited'])

    def test_custom_monthly_limit_is_enforced(self):
        CherryChinaPlan.objects.create(user=self.user, monthly_report_limit=2)
        CherryChinaReport.objects.create(user=self.user, status='COMPLETED')

        quota = get_account_quota(self.user)
        self.assertEqual(quota['plan'], 'CUSTOM')
        self.assertEqual(quota['limit'], 2)
        self.assertEqual(quota['remaining'], 1)
        reserve_report(self.user, '176264', '')

        with self.assertRaises(ReportQuotaExceeded):
            reserve_report(self.user, '176264', '')

    def test_custom_zero_limit_blocks_reports(self):
        CherryChinaPlan.objects.create(user=self.user, monthly_report_limit=0)

        with self.assertRaises(ReportQuotaExceeded):
            reserve_report(self.user, '176264', '')

    def test_admin_can_set_user_limit_or_unlimited_access(self):
        admin_user = User.objects.create_user(username='quota-admin', password='test-password')
        UserProfile.objects.create(user=admin_user, role='SUPERADMIN')
        client = APIClient()
        client.force_authenticate(admin_user)

        response = client.patch(
            f'/api/cherry-china/admin/users/{self.user.pk}/',
            {'unlimited': False, 'monthly_limit': 12},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['quota']['limit'], 12)
        self.assertEqual(response.data['user']['quota']['plan'], 'CUSTOM')

        response = client.patch(
            f'/api/cherry-china/admin/users/{self.user.pk}/',
            {'unlimited': True},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data['user']['quota']['unlimited'])

    def test_regular_user_cannot_manage_user_quotas(self):
        client = APIClient()
        client.force_authenticate(self.user)

        response = client.get('/api/cherry-china/admin/users/')

        self.assertEqual(response.status_code, 403)

    def test_admin_cannot_assign_negative_limit(self):
        admin_user = User.objects.create_user(username='quota-admin', password='test-password')
        UserProfile.objects.create(user=admin_user, role='SUPERADMIN')
        client = APIClient()
        client.force_authenticate(admin_user)

        response = client.patch(
            f'/api/cherry-china/admin/users/{self.user.pk}/',
            {'unlimited': False, 'monthly_limit': -1},
            format='json',
        )

        self.assertEqual(response.status_code, 400)


class CherryChinaSourceRuleTests(TestCase):
    def test_pdf_places_two_csgs_on_each_letter_page(self):
        csgs = [
            {'code': code, 'producer_name': f'Productor {code}', 'establishment_name': f'Predio {code}', 'active': True, 'species': ['CEREZA'], 'varieties': ['BING'], 'mosca_campaigns': [], 'descolgado_china': False, 'descolgados': []}
            for code in ('176264', '176265', '176266')
        ]
        report = SimpleNamespace(pk=99, csg='176264', csp='', csgs=[item['code'] for item in csgs])
        pdf_bytes = build_validation_pdf(
            report,
            {'csg': csgs[0], 'csgs': csgs, 'csp': {'code': ''}},
            [{'name': 'SRA', 'status': 'ok'}],
        )

        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            self.assertEqual(len(pdf.pages), 2)
            first_page = pdf.pages[0].extract_text() or ''
            second_page = pdf.pages[1].extract_text() or ''
        self.assertIn('176264', first_page)
        self.assertIn('176265', first_page)
        self.assertIn('176266', second_page)
        self.assertEqual(first_page.count('Sin descolgados cereza-China'), 2)

    @patch('cherry_china_validation.sources.sync_playwright')
    @patch('cherry_china_validation.sources._run_single_cherry_china_check')
    def test_many_csgs_are_checked_separately_and_sources_are_merged(self, run_single, playwright_factory):
        context = MagicMock()
        context.new_page.side_effect = [MagicMock(), MagicMock(), MagicMock()]
        browser = MagicMock()
        browser.new_context.return_value = context
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser
        manager = MagicMock()
        manager.__enter__.return_value = playwright
        manager.__exit__.return_value = False
        playwright_factory.return_value = manager
        run_single.side_effect = [
            (
                {'csg': {'code': '176264'}, 'csp': {'code': '175848'}, 'chinaport': {}},
                [{'name': 'SRA', 'status': 'ok', 'found': True}, {'name': 'China-CSP', 'status': 'ok'}],
            ),
            (
                {'csg': {'code': '176265'}, 'csp': {'code': ''}, 'chinaport': {}},
                [{'name': 'SRA', 'status': 'unavailable'}, {'name': 'China-CSG', 'status': 'ok', 'found': True}],
            ),
            (
                {'csg': {'code': '176266'}, 'csp': {'code': ''}, 'chinaport': {}},
                [{'name': 'SRA', 'status': 'ok', 'found': True}, {'name': 'China-CSG', 'status': 'ok', 'found': True}],
            ),
        ]

        results, sources = run_cherry_china_checks(csp='175848', csgs=['176264', '176265', '176266'])

        self.assertEqual([item['code'] for item in results['csgs']], ['176264', '176265', '176266'])
        self.assertEqual(results['csp']['code'], '175848')
        self.assertEqual(run_single.call_args_list[0].args, ('176264', '175848'))
        self.assertEqual(run_single.call_args_list[1].args, ('176265', ''))
        self.assertEqual(run_single.call_args_list[2].args, ('176266', ''))
        self.assertIs(run_single.call_args_list[0].kwargs['pages'], run_single.call_args_list[1].kwargs['pages'])
        self.assertIs(run_single.call_args_list[1].kwargs['pages'], run_single.call_args_list[2].kwargs['pages'])
        self.assertEqual(next(item for item in sources if item['name'] == 'SRA')['status'], 'partial')
        self.assertEqual(next(item for item in sources if item['name'] == 'China-CSP')['codes'], ['175848'])

    @patch('cherry_china_validation.sources.sync_playwright')
    @patch('cherry_china_validation.sources._run_single_cherry_china_check')
    def test_multiple_csps_are_returned_as_distinct_results(self, run_single, playwright_factory):
        context = MagicMock()
        context.new_page.side_effect = [MagicMock(), MagicMock(), MagicMock()]
        browser = MagicMock()
        browser.new_context.return_value = context
        playwright = MagicMock()
        playwright.chromium.launch.return_value = browser
        manager = MagicMock()
        manager.__enter__.return_value = playwright
        manager.__exit__.return_value = False
        playwright_factory.return_value = manager
        csp_results = [
            {'code': '175848', 'china_registered': True, 'china_approved': False, 'mosca_campaigns': [{'campaign': 'Carén', 'country': 'China'}]},
            {'code': '175849', 'china_registered': True, 'china_approved': True, 'mosca_campaigns': [{'campaign': 'Dos Ríos', 'country': 'Corea'}]},
        ]
        run_single.return_value = (
            {'csg': {'code': ''}, 'csp': csp_results[0], 'csps': csp_results},
            [{'name': 'China-CSP', 'status': 'ok', 'codes': ['175848', '175849']}],
        )

        results, sources = run_cherry_china_checks(csps=['175848', '175849'])

        self.assertEqual([item['code'] for item in results['csps']], ['175848', '175849'])
        self.assertEqual(results['csp']['code'], '175848')
        self.assertEqual(sources[0]['codes'], ['175848', '175849'])

    def test_cherry_species_and_varieties_are_not_redundant(self):
        species, varieties = parse_cherry_species([
            'CEREZA - BING',
            'CEREZA - KORDIA',
            'CEREZA - BING',
            'MANZANA - GALA',
        ])

        self.assertEqual(species, ['CEREZA'])
        self.assertEqual(varieties, ['BING', 'KORDIA'])

    def test_chinaport_exact_csg_with_cherry_and_active_valid_record_is_approved(self):
        result = summarize_chinaport_rows([
            {
                'overseasOfficialRegNo': '176264',
                'prodNameEn': 'Cherry',
                'prodNameLa': 'Prunus avium',
                'regState': '1',
                'validFrom': '2024-05-27',
                'validTo': '2999-12-31',
            }
        ], '176264', today=timezone.now().date())

        self.assertTrue(result['verified'])
        self.assertTrue(result['china_cherry_approved'])
        self.assertEqual(result['scientific_name'], 'Prunus avium')
        self.assertEqual(result['registration_status'], 'Normal (vigente)')

    def test_chinaport_multiple_products_keeps_only_cherry_and_matching_scientific_name(self):
        result = summarize_chinaport_rows([
            {
                'overseasOfficialRegNo': '95933',
                'prodNameEn': 'Plum\nCHERRY\nNECTARINES',
                'prodNameCn': '李\n樱桃\n油桃',
                'prodNameLa': 'Prunus salicina\nPrunus domestica\nPrunus avium',
                'regState': '1',
                'validFrom': '2024-05-27 00:00:01',
                'validTo': '2999-12-31 23:59:59',
            }
        ], '95933', today=timezone.now().date())

        self.assertTrue(result['china_cherry_approved'])
        self.assertEqual(result['product_name'], 'Cherry')
        self.assertEqual(result['scientific_name'], 'Prunus avium')

    def test_chinaport_other_product_or_inactive_record_is_not_approved(self):
        rows = [
            {
                'overseasOfficialRegNo': '176264',
                'prodNameEn': 'Apple',
                'regState': '1',
                'validFrom': '2024-05-27',
                'validTo': '2999-12-31',
            },
            {
                'overseasOfficialRegNo': '176265',
                'prodNameEn': 'Cherry',
                'regState': '2',
                'validFrom': '2024-05-27',
                'validTo': '2999-12-31',
            },
        ]
        self.assertFalse(summarize_chinaport_rows(rows, '176264')['china_cherry_approved'])
        self.assertFalse(summarize_chinaport_rows(rows, '176265')['china_cherry_approved'])

    def test_chinaport_expired_record_is_not_approved(self):
        result = summarize_chinaport_rows([
            {
                'overseasOfficialRegNo': '176264',
                'prodNameEn': 'Cherry',
                'regState': '1',
                'validFrom': '2020-01-01',
                'validTo': '2025-12-31',
            }
        ], '176264', today=timezone.now().date())
        self.assertFalse(result['china_cherry_approved'])

    def test_powerbi_cherry_report_maps_csg_column_order_by_header(self):
        result = _map_powerbi_row(
            ['Row Selection', 'CSG', 'COMUNA', 'REGIÓN'],
            ['Select Row', '176264', 'MOLINA', 'DEL MAULE'],
            '176264',
            'CSG',
        )
        self.assertTrue(result['found'])
        self.assertEqual(result['commune'], 'MOLINA')
        self.assertEqual(result['region'], 'DEL MAULE')

    def test_powerbi_cherry_report_maps_csp_column_order_by_header(self):
        result = _map_powerbi_row(
            ['Row Selection', 'CSP', 'NOMBRE ESTABLECIMIENTO', 'REGIÓN', 'COMUNA'],
            ['Select Row', '175848', 'PACKING TEST', 'O HIGGINS', 'RENGO'],
            '175848',
            'CSP',
        )
        self.assertTrue(result['found'])
        self.assertEqual(result['establishment_name'], 'PACKING TEST')
        self.assertEqual(result['region'], 'O HIGGINS')
        self.assertEqual(result['commune'], 'RENGO')

    def test_descolgados_parser_uses_target_country_not_detection_country(self):
        cells = [
            '4', 'SAN FRANCISCO', 'GF MALLOA', '11.347.673-7',
            'ISABEL URETA EDWARDS', '175760', 'QUINTA DE TILCOCO',
            'CEREZAS', 'ROYAL DAWN', 'EN INSPECCIÓN', 'CHINA',
            'PERU (VARIEDAD SOLO CON FUMIGACIÓN)', 'DROSOPHILA SUZUKII', 'VARIEDAD',
        ]
        row = map_descolgados_cells(cells)
        result = summarize_descolgados([row], '175760')

        self.assertEqual(row['country_detected'], 'CHINA')
        self.assertEqual(row['country_to_remove'], 'PERU (VARIEDAD SOLO CON FUMIGACIÓN)')
        self.assertEqual(row['pest'], 'DROSOPHILA SUZUKII')
        self.assertFalse(result['descolgado_china'])

    def test_campaign_status_uses_all_rows_and_lists_only_current_pairs(self):
        result = summarize_campaign_rows([
            {'campaign': 'Dos Ríos', 'country': 'China', 'current': 'NO'},
            {'campaign': 'Carén', 'country': 'China', 'current': 'SI'},
            {'campaign': 'Carén', 'country': 'China', 'current': 'SI'},
            {'campaign': 'Carén', 'country': 'Perú', 'current': 'SI'},
        ])

        self.assertTrue(result['found'])
        self.assertTrue(result['current'])
        self.assertEqual(len(result['campaigns']), 2)
        self.assertEqual(result['campaigns'][0], {'campaign': 'Carén', 'country': 'China'})

    def test_campaign_status_ignores_powerbi_conditional_formatting_suffix(self):
        result = summarize_campaign_rows([
            {'campaign': 'BODEGA', 'country': 'CHINA', 'current': 'SIAdditional Conditional Formatting'},
        ])

        self.assertTrue(result['current'])
        self.assertEqual(result['campaigns'], [{'campaign': 'BODEGA', 'country': 'CHINA'}])

    def test_no_current_campaign_is_different_from_not_found(self):
        self.assertEqual(
            summarize_campaign_rows([{'campaign': 'Dos Ríos', 'country': 'China', 'current': 'NO'}]),
            {'found': True, 'current': False, 'campaigns': []},
        )
        self.assertEqual(
            summarize_campaign_rows([]),
            {'found': False, 'current': False, 'campaigns': []},
        )

    def test_peru_only_cherry_detection_does_not_flag_china(self):
        result = summarize_descolgados([
            {
                'csg': '175760',
                'species': 'CEREZAS',
                'variety': 'ROYAL DAWN',
                'pest': 'DROSOPHILA SUZUKII',
                'country_to_remove': 'PERU (VARIEDAD SOLO CON FUMIGACIÓN)',
            }
        ], '175760')

        self.assertFalse(result['descolgado_china'])
        self.assertEqual(result['detections'], [])

    def test_other_species_are_not_cherry_china_detections(self):
        result = summarize_descolgados([
            {
                'csg': '175760',
                'species': 'MANZANAS',
                'variety': 'GALA',
                'pest': 'PEST',
                'country_to_remove': 'CHINA',
            }
        ], '175760')

        self.assertFalse(result['descolgado_china'])

    def test_cherry_detection_targeting_china_is_reported(self):
        result = summarize_descolgados([
            {
                'csg': '175760',
                'species': 'CEREZAS',
                'variety': 'SANTINA',
                'pest': 'DROSOPHILA SUZUKII',
                'country_to_remove': 'CHINA, PERÚ',
            }
        ], '175760')

        self.assertTrue(result['descolgado_china'])
        self.assertEqual(result['detections'][0]['variety'], 'SANTINA')


class CherryChinaApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='api-test', password='test-password')
        self.client = APIClient()

    def test_validation_requires_authentication(self):
        response = self.client.post('/api/cherry-china/validate/', {'csg': '176264'}, format='json')
        self.assertEqual(response.status_code, 401)

    @patch('cherry_china_validation.views.build_validation_pdf', return_value=b'%PDF-regenerated')
    def test_pdf_download_regenerates_missing_worker_file_from_saved_results(self, build_pdf):
        report = CherryChinaReport.objects.create(
            user=self.user,
            status='COMPLETED',
            results={'csg': {'code': '176264'}},
            sources=[{'name': 'SRA', 'status': 'ok'}],
        )
        self.client.force_authenticate(self.user)

        response = self.client.get(f'/api/cherry-china/reports/{report.pk}/pdf/')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(b''.join(response.streaming_content), b'%PDF-regenerated')
        build_pdf.assert_called_once()
        report.refresh_from_db()
        self.assertEqual(bytes(report.pdf_data), b'%PDF-regenerated')

    def test_invalid_code_is_rejected_before_creating_report(self):
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/cherry-china/validate/', {'csg': '17626A'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertEqual(CherryChinaReport.objects.count(), 0)

    @patch('cherry_china_validation.worker.run_cherry_china_checks')
    def test_many_csgs_and_csps_create_one_report_with_pages(self, run_checks):
        run_checks.return_value = (
            {
                'csg': {'code': '176264', 'species': ['CEREZA'], 'varieties': ['BING']},
                'csgs': [
                    {'code': '176264', 'species': ['CEREZA'], 'varieties': ['BING']},
                    {'code': '176265', 'species': ['CEREZA'], 'varieties': ['SANTINA']},
                    {'code': '176266', 'species': ['CEREZA'], 'varieties': ['LAPINS']},
                ],
                'csp': {'code': '175848', 'china_registered': True, 'china_approved': False},
                'csps': [
                    {'code': '175848', 'china_registered': True, 'china_approved': False},
                    {'code': '175849', 'china_registered': True, 'china_approved': True},
                ],
                'chinaport': [],
            },
            [{'name': 'SRA', 'status': 'ok'}],
        )
        self.client.force_authenticate(self.user)

        with TemporaryDirectory() as media_dir:
            with override_settings(MEDIA_ROOT=media_dir):
                response = self.client.post(
                    '/api/cherry-china/validate/',
                    {'csgs': ['176264', '176265', '176266'], 'csps': ['175848', '175849']},
                    format='json',
                )

                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.data['status'], 'QUEUED')
                self.assertEqual(response.data['quota']['remaining'], FREE_REPORT_LIMIT - 1)
                report = CherryChinaReport.objects.get(user=self.user)
                self.assertEqual(report.csgs, ['176264', '176265', '176266'])
                self.assertEqual(report.csps, ['175848', '175849'])
                self.assertEqual(report.status, 'QUEUED')
                run_checks.assert_not_called()

                self.assertEqual(claim_next_report(), report.pk)
                report = process_report(report.pk)
                self.assertEqual(report.status, 'COMPLETED')
                run_checks.assert_called_once()

                status_response = self.client.get(f'/api/cherry-china/reports/{report.pk}/status/')
                self.assertEqual(status_response.data['status'], 'COMPLETED')
                pdf_response = self.client.get(f'/api/cherry-china/reports/{report.pk}/pdf/')
                pdf_body = b''.join(pdf_response.streaming_content)
                with pdfplumber.open(BytesIO(pdf_body)) as pdf:
                    self.assertEqual(len(pdf.pages), 2)
                    page_text = [page.extract_text() or '' for page in pdf.pages]
                self.assertIn('176264', page_text[0])
                self.assertIn('176265', page_text[0])
                self.assertIn('176266', page_text[1])
                self.assertIn('175848', page_text[0])
                self.assertIn('175849', page_text[0])
                report.pdf_file.delete(save=False)

        self.assertEqual(response.status_code, 202)
        self.assertEqual(response.data['quota']['remaining'], FREE_REPORT_LIMIT - 1)
        report = CherryChinaReport.objects.get(user=self.user)
        self.assertEqual(report.csgs, ['176264', '176265', '176266'])
        run_checks.assert_called_once()

    @patch('cherry_china_validation.worker.run_cherry_china_checks')
    def test_success_creates_user_owned_pdf_report(self, run_checks):
        run_checks.return_value = (
            {
                'csg': {
                    'code': '176264',
                    'active': True,
                    'producer_name': 'Productor de prueba',
                    'establishment_name': 'Predio de prueba',
                    'species': ['CEREZA'],
                    'varieties': ['BING'],
                    'china_registered': True,
                    'china_cherry_approved': True,
                    'chinaport_product_name': 'Cherry',
                    'chinaport_scientific_name': 'Prunus avium',
                    'chinaport_registration_status': 'Normal (vigente)',
                    'chinaport_registration_expiry': '2999-12-31 00:00:00',
                    'mosca_campaign_found': False,
                    'mosca_campaign_current': False,
                    'mosca_campaigns': [],
                    'descolgado_china': False,
                    'descolgados': [],
                },
                'csp': {'code': '', 'china_registered': None, 'china_approved': None, 'mosca_campaign_current': None, 'mosca_campaigns': []},
                'chinaport': {'csg': None, 'csp': None},
            },
            [{'name': 'SRA', 'status': 'ok'}],
        )
        self.client.force_authenticate(self.user)

        with TemporaryDirectory() as media_dir:
            with override_settings(MEDIA_ROOT=media_dir):
                response = self.client.post('/api/cherry-china/validate/', {'csg': '176264'}, format='json')

                self.assertEqual(response.status_code, 202)
                self.assertEqual(response.data['status'], 'QUEUED')
                self.assertEqual(response.data['quota']['remaining'], FREE_REPORT_LIMIT - 1)
                report = CherryChinaReport.objects.get(pk=response.data['report_id'], user=self.user)
                self.assertEqual(report.status, 'QUEUED')
                run_checks.assert_not_called()
                self.assertEqual(claim_next_report(), report.pk)
                report = process_report(report.pk)
                self.assertEqual(report.status, 'COMPLETED')
                self.assertTrue(bytes(report.pdf_data).startswith(b'%PDF'))
                self.assertFalse(report.pdf_file)
                run_checks.assert_called_once()
                status_response = self.client.get(f'/api/cherry-china/reports/{report.pk}/status/')
                self.assertEqual(status_response.data['status'], 'COMPLETED')

                pdf_response = self.client.get(f'/api/cherry-china/reports/{report.pk}/pdf/')
                self.assertEqual(pdf_response.status_code, 200)
                pdf_body = b''.join(pdf_response.streaming_content)
                self.assertTrue(pdf_body.startswith(b'%PDF'))
                with pdfplumber.open(BytesIO(pdf_body)) as pdf:
                    self.assertEqual(len(pdf.pages), 1)
                    pdf_text = '\n'.join(page.extract_text() or '' for page in pdf.pages)
                self.assertIn('CEREZA', pdf_text)
                self.assertIn('BING', pdf_text)
                self.assertNotIn('2999-12-31', pdf_text)
                report.pdf_file.delete(save=False)