from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor
from threading import Barrier
from unittest import skipUnless
from unittest.mock import patch

from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import close_old_connections, connection, connections
from django.test import TestCase, TransactionTestCase
from django.utils import timezone
from rest_framework.test import APIClient

from .models import Establishment, EstablishmentPlan, PlanBatchArtifact, PlanUsage, UserProfile
from .plan_usage import PlanUsageError, assign_plan, finish_usage, plan_summary, reserve_usage, reset_free


class PlanUsageTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='plan-user')
        self.establishment = Establishment.objects.create(
            planta_fruticola='Test', license_key='plan-test'
        )
        UserProfile.objects.create(user=self.user, establishment=self.establishment)

    def test_requires_manual_assignment(self):
        with self.assertRaises(PlanUsageError):
            reserve_usage(self.user, 'sdp')

    def test_free_rolling_limit_cancel_and_reset(self):
        plan = assign_plan(self.establishment, 'FREE')
        first = reserve_usage(self.user, 'print')
        finish_usage(first, True)
        cancelled = reserve_usage(self.user, 'sdp')
        finish_usage(cancelled, False)
        second = reserve_usage(self.user, 'diagram')
        finish_usage(second, True)
        with self.assertRaises(PlanUsageError):
            reserve_usage(self.user, 'china')
        first.refresh_from_db()
        second.refresh_from_db()
        now = timezone.now()
        PlanUsage.objects.filter(pk=first.pk).update(completed_at=now - timedelta(hours=24, seconds=1))
        with patch('inspections.plan_usage.timezone.now', return_value=now):
            self.assertEqual(plan_summary(plan)['remaining'], 1)
        reset_free(self.establishment)
        plan.refresh_from_db()
        self.assertEqual(plan_summary(plan)['remaining'], 2)

    def test_starter_changes_to_free_after_150_successes(self):
        plan = assign_plan(self.establishment, 'STARTER')
        PlanUsage.objects.bulk_create([
            PlanUsage(
                establishment=self.establishment, user=self.user, plan='STARTER',
                activation=plan.activated_at, operation='sdp', status='COMPLETED',
                completed_at=timezone.now(),
            )
            for _ in range(149)
        ])
        usage = reserve_usage(self.user, 'sdp')
        finish_usage(usage, True)
        plan.refresh_from_db()
        self.assertEqual(plan.plan, 'FREE')
        self.assertIn('Starter', plan.alert_message)
        self.assertEqual(plan_summary(plan)['remaining'], 2)

    def test_pro_expires_after_30_days(self):
        plan = assign_plan(self.establishment, 'PRO')
        with patch('inspections.plan_usage.timezone.now', return_value=plan.activated_at + timedelta(days=30)):
            summary = plan_summary(plan)
        self.assertEqual(summary['plan'], 'FREE')
        self.assertEqual(summary['remaining'], 2)
        self.assertIn('Pro', plan.alert_message)

    def test_free_reset_cancels_pending_operations(self):
        assign_plan(self.establishment, 'FREE')
        usage = reserve_usage(self.user, 'print')
        reset_free(self.establishment)
        usage.refresh_from_db()
        self.assertEqual(usage.status, 'CANCELLED')
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 2)

    def test_expired_abandoned_batch_releases_reservation(self):
        plan = assign_plan(self.establishment, 'FREE')
        usage = reserve_usage(self.user, 'batch_pdf')
        PlanUsage.objects.filter(pk=usage.pk).update(created_at=timezone.now() - timedelta(hours=2))
        self.assertEqual(plan_summary(plan)['remaining'], 2)
        self.assertFalse(finish_usage(usage, True))

    def test_reassignment_and_reset_prevent_old_success(self):
        assign_plan(self.establishment, 'FREE')
        usage = reserve_usage(self.user, 'print')
        assign_plan(self.establishment, 'STARTER')
        self.assertFalse(finish_usage(usage, True))
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 150)


class PlanApiTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='plan-api', password='test-password')
        self.establishment = Establishment.objects.create(planta_fruticola='Test', license_key='plan-api')
        UserProfile.objects.create(user=self.user, establishment=self.establishment)
        self.client = APIClient()

    def test_login_expired_legacy_subscription_and_acknowledge_alert(self):
        self.establishment.subscription_status = 'EXPIRED'
        self.establishment.save()
        plan = assign_plan(self.establishment, 'PRO')
        plan.activated_at = timezone.now() - timedelta(days=31)
        plan.save(update_fields=['activated_at'])
        credentials = {'username': self.user.username, 'password': 'test-password'}
        first = self.client.post('/api/auth/login/', credentials, format='json')
        self.assertEqual(first.status_code, 200)
        alert = first.data['user']['plan_alert']
        self.assertIn('Pro', alert)
        second = self.client.post('/api/auth/login/', credentials, format='json')
        self.assertEqual(second.data['user']['plan_alert'], alert)
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/plans/alert/acknowledge/', {'message': alert}, format='json')
        self.assertEqual(response.status_code, 200)
        plan.refresh_from_db()
        self.assertEqual(plan.alert_message, '')

    def test_suspended_account_cannot_login_or_reserve(self):
        assign_plan(self.establishment, 'FREE')
        self.establishment.subscription_status = 'SUSPENDED'
        self.establishment.save()
        response = self.client.post('/api/auth/login/', {'username': self.user.username, 'password': 'test-password'}, format='json')
        self.assertEqual(response.status_code, 400)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post('/api/plans/reserve/', {'operation': 'print'}, format='json').status_code, 403)

    def test_reservations_are_user_owned_and_finish_idempotently(self):
        assign_plan(self.establishment, 'FREE')
        other = User.objects.create_user(username='other')
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/plans/reserve/', {'operation': 'diagram'}, format='json')
        reservation = response.data['reservation_id']
        url = f'/api/plans/reservations/{reservation}/finish/'
        self.client.force_authenticate(other)
        self.assertEqual(self.client.post(url, {'succeeded': True}, format='json').status_code, 404)
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post(url, {'succeeded': True}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'succeeded': True}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'succeeded': False}, format='json').status_code, 409)
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 1)

    def test_interrupted_print_is_counted_but_rejection_is_released(self):
        plan = assign_plan(self.establishment, 'FREE')
        self.client.force_authenticate(self.user)
        first = self.client.post('/api/plans/reserve/', {'operation': 'print'}, format='json').data['reservation_id']
        dispatch = f'/api/plans/reservations/{first}/dispatch-print/'
        self.assertEqual(self.client.post(dispatch).status_code, 200)
        PlanUsage.objects.filter(pk=first).update(created_at=timezone.now() - timedelta(hours=2))
        self.assertEqual(plan_summary(plan)['remaining'], 1)
        self.assertEqual(PlanUsage.objects.get(pk=first).status, 'COMPLETED')
        second = self.client.post('/api/plans/reserve/', {'operation': 'print'}, format='json').data['reservation_id']
        self.assertEqual(self.client.post(f'/api/plans/reservations/{second}/dispatch-print/').status_code, 200)
        self.assertEqual(self.client.post(f'/api/plans/reservations/{second}/finish/', {'succeeded': False}, format='json').status_code, 200)
        self.assertEqual(plan_summary(plan)['remaining'], 1)

    def test_interrupted_print_does_not_restart_free_window_when_recovered_late(self):
        plan = assign_plan(self.establishment, 'FREE')
        self.client.force_authenticate(self.user)
        usage = reserve_usage(self.user, 'print')
        self.client.post(f'/api/plans/reservations/{usage.pk}/dispatch-print/')
        PlanUsage.objects.filter(pk=usage.pk).update(created_at=timezone.now() - timedelta(hours=26))
        self.assertEqual(plan_summary(plan)['remaining'], 2)
        usage.refresh_from_db()
        self.assertEqual(usage.status, 'COMPLETED')

    def test_dispatch_requires_owner_and_active_establishment(self):
        assign_plan(self.establishment, 'FREE')
        usage = reserve_usage(self.user, 'print')
        url = f'/api/plans/reservations/{usage.pk}/dispatch-print/'
        self.client.force_authenticate(User.objects.create_user(username='other'))
        self.assertEqual(self.client.post(url).status_code, 404)
        self.client.force_authenticate(self.user)
        self.establishment.subscription_status = 'SUSPENDED'
        self.establishment.save()
        self.assertEqual(self.client.post(url).status_code, 403)

    def test_batch_download_is_private_and_charged_once(self):
        assign_plan(self.establishment, 'FREE')
        usage = reserve_usage(self.user, 'batch_pdf')
        artifact = PlanBatchArtifact.objects.create(user=self.user, usage=usage, filename='test.pdf', data=b'%PDF-test')
        url = f'/api/plans/batch-pdf/{artifact.pk}/'
        self.assertEqual(self.client.get(url).status_code, 401)
        self.client.force_authenticate(User.objects.create_user(username='other'))
        self.assertEqual(self.client.get(url).status_code, 404)
        self.client.force_authenticate(self.user)
        for _ in range(2):
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(b''.join(response.streaming_content), b'%PDF-test')
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 1)

    def test_batch_generation_then_download_charges_only_on_download(self):
        assign_plan(self.establishment, 'FREE')
        self.client.force_authenticate(self.user)
        response = self.client.post('/api/batch-description/save-batch/', {
            'header': {'sif': '123'}, 'pallets': [{'folio_pallet': '1', 'cajas': 10}],
            'especie': 'CEREZA', 'type': 'NORMAL',
        }, format='json')
        self.assertEqual(response.status_code, 200)
        artifact = PlanBatchArtifact.objects.get(user=self.user)
        artifact.usage.refresh_from_db()
        self.assertEqual(artifact.usage.status, 'RESERVED')
        response = self.client.get(f'/api/plans/batch-pdf/{artifact.pk}/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue(b''.join(response.streaming_content).startswith(b'%PDF'))
        artifact.usage.refresh_from_db()
        self.assertEqual(artifact.usage.status, 'COMPLETED')
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 1)

    def test_only_admin_can_assign_plans(self):
        self.client.force_authenticate(self.user)
        url = f'/api/admin/establishments/{self.establishment.pk}/assign_plan/'
        self.assertEqual(self.client.post(url, {'plan': 'PRO'}, format='json').status_code, 403)
        admin = User.objects.create_user(username='plan-admin')
        UserProfile.objects.create(user=admin, role='SUPERADMIN')
        self.client.force_authenticate(admin)
        response = self.client.post(url, {'plan': 'STARTER'}, format='json')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['remaining'], 150)

    def test_assigned_plans_are_persisted_in_establishment_plan_list(self):
        admin = User.objects.create_user(username='listing-admin')
        UserProfile.objects.create(user=admin, role='SUPERADMIN')
        self.client.force_authenticate(admin)
        url = f'/api/admin/establishments/{self.establishment.pk}/assign_plan/'
        for name, remaining in [('FREE', 2), ('STARTER', 150), ('PRO', None)]:
            with self.subTest(plan=name):
                response = self.client.post(url, {'plan': name}, format='json')
                self.assertEqual(response.status_code, 200)
                response = self.client.get('/api/admin/establishments/plans/')
                self.assertEqual(response.status_code, 200)
                plan = next(item['plan'] for item in response.data if item['id'] == self.establishment.pk)
                self.assertEqual(plan['plan'], name)
                self.assertEqual(plan['remaining'], remaining)

    def test_legacy_renewal_does_not_unsuspend_or_claim_to_renew_plan(self):
        assign_plan(self.establishment, 'FREE')
        self.establishment.subscription_status = 'SUSPENDED'
        self.establishment.save()
        admin = User.objects.create_user(username='legacy-admin')
        UserProfile.objects.create(user=admin, role='SUPERADMIN')
        self.client.force_authenticate(admin)
        url = f'/api/admin/establishments/{self.establishment.pk}/renew_subscription/'
        self.assertEqual(self.client.post(url, {'days': 30}, format='json').status_code, 410)
        self.establishment.refresh_from_db()
        self.assertEqual(self.establishment.subscription_status, 'SUSPENDED')
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['plan'], 'FREE')

    def test_only_admin_can_resolve_old_uncertain_operations(self):
        plan = assign_plan(self.establishment, 'STARTER')
        usage = reserve_usage(self.user, 'sdp')
        url = f'/api/admin/establishments/{self.establishment.pk}/pending_usages/'
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.get(url).status_code, 403)
        admin = User.objects.create_user(username='pending-admin')
        UserProfile.objects.create(user=admin, role='SUPERADMIN')
        self.client.force_authenticate(admin)
        self.assertEqual(self.client.get(url).data, [])
        self.assertEqual(self.client.post(url, {'usage_id': usage.pk, 'succeeded': False}, format='json').status_code, 409)
        PlanUsage.objects.filter(pk=usage.pk).update(created_at=timezone.now() - timedelta(hours=2))
        self.assertEqual(self.client.get(url).data[0]['id'], usage.pk)
        self.assertEqual(self.client.post(url, {'usage_id': usage.pk, 'succeeded': False}, format='json').status_code, 200)
        self.assertEqual(self.client.post(url, {'usage_id': usage.pk, 'succeeded': True}, format='json').status_code, 409)
        self.assertEqual(plan_summary(plan)['remaining'], 150)
        self.assertFalse(finish_usage(usage, True))

    @patch('inspections.sdp_validation_views.SagSdpService')
    @patch('inspections.sdp_validation_views.parse_sdp_workbook')
    def test_sdp_success_consumes_one_use_and_failure_releases(self, parse, service):
        assign_plan(self.establishment, 'FREE')
        self.client.force_authenticate(self.user)
        parse.return_value = {
            'errors': [], 'unique_sdps': ['123'],
            'rows': [{'sdp': '123', 'csg': '1', 'provincia': '', 'comuna': '', 'variedad_rotulada': ''}],
            'metadata': {}, 'sheets': [],
        }
        url = '/api/batch-description/validate-sdp-excel/'
        service.return_value.query.return_value = {'status': 'NOT_FOUND', 'datos': None}
        response = self.client.post(url, {'file': SimpleUploadedFile('test.xlsx', b'excel')})
        self.assertEqual(response.status_code, 200)
        pdf_url = response.data['pdf_url']
        download = self.client.get(pdf_url)
        self.assertEqual(download.status_code, 200)
        self.assertTrue(b''.join(download.streaming_content).startswith(b'%PDF-'))
        other = User.objects.create_user(username='other-sdp')
        self.client.force_authenticate(other)
        self.assertEqual(self.client.get(pdf_url).status_code, 404)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get(pdf_url).status_code, 401)
        self.client.force_authenticate(self.user)
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 1)
        service.return_value.query.return_value = {'status': 'ERROR', 'datos': None}
        response = self.client.post(url, {'file': SimpleUploadedFile('test.xlsx', b'excel')})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(plan_summary(self.establishment.commercial_plan)['remaining'], 1)


@skipUnless(connection.vendor == 'postgresql', 'Requiere PostgreSQL para verificar bloqueos reales.')
class PlanConcurrencyTests(TransactionTestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='concurrent-plan')
        self.establishment = Establishment.objects.create(planta_fruticola='Test', license_key='concurrent-plan')
        UserProfile.objects.create(user=self.user, establishment=self.establishment)
        assign_plan(self.establishment, 'FREE')

    def run_concurrently(self, functions):
        barrier = Barrier(len(functions))

        def run(function):
            close_old_connections()
            try:
                with connections['default'].cursor() as cursor:
                    cursor.execute("SET lock_timeout = '10s'")
                barrier.wait(timeout=10)
                return function()
            finally:
                connections.close_all()

        with ThreadPoolExecutor(max_workers=len(functions)) as executor:
            futures = [executor.submit(run, function) for function in functions]
            return [future.result(timeout=30) for future in futures]

    def test_three_simultaneous_reservations_cannot_exceed_free_limit(self):
        def reserve():
            try:
                return reserve_usage(User.objects.get(pk=self.user.pk), 'diagram').pk
            except PlanUsageError:
                return None

        results = self.run_concurrently([reserve, reserve, reserve])
        self.assertEqual(sum(result is not None for result in results), 2)
        self.assertEqual(PlanUsage.objects.filter(status='RESERVED').count(), 2)

    def test_reassignment_racing_completion_never_charges_new_activation(self):
        usage = reserve_usage(self.user, 'diagram')
        self.run_concurrently([
            lambda: finish_usage(usage, True),
            lambda: assign_plan(Establishment.objects.get(pk=self.establishment.pk), 'STARTER'),
        ])
        usage.refresh_from_db()
        self.assertIn(usage.status, ('COMPLETED', 'CANCELLED'))
        self.assertEqual(plan_summary(EstablishmentPlan.objects.get(establishment=self.establishment))['remaining'], 150)

    def test_reset_racing_completion_keeps_free_reset_effective(self):
        usage = reserve_usage(self.user, 'diagram')
        self.run_concurrently([
            lambda: finish_usage(usage, True),
            lambda: reset_free(Establishment.objects.get(pk=self.establishment.pk)),
        ])
        self.assertEqual(plan_summary(EstablishmentPlan.objects.get(establishment=self.establishment))['remaining'], 2)

    def test_worker_completion_racing_timeout_does_not_deadlock_or_double_charge(self):
        from cherry_china_validation.models import CherryChinaReport
        from cherry_china_validation.quota import reserve_report
        from cherry_china_validation.worker import claim_next_report, process_report

        report = reserve_report(self.user, '176264', '')
        self.assertEqual(claim_next_report(), report.pk)
        CherryChinaReport.objects.filter(pk=report.pk).update(started_at=timezone.now() - timedelta(hours=2))
        with patch('cherry_china_validation.worker.run_cherry_china_checks', return_value=(
            {'csg': {'code': '176264'}}, [{'name': 'SRA', 'status': 'ok'}],
        )), patch('cherry_china_validation.worker.build_validation_pdf', return_value=b'%PDF'):
            self.run_concurrently([
                lambda: process_report(report.pk),
                lambda: plan_summary(EstablishmentPlan.objects.get(establishment=self.establishment)),
            ])
        report.refresh_from_db()
        report.plan_usage.refresh_from_db()
        self.assertIn(
            (report.status, report.plan_usage.status),
            [('COMPLETED', 'COMPLETED'), ('FAILED', 'CANCELLED')],
        )
        self.assertEqual(
            plan_summary(EstablishmentPlan.objects.get(establishment=self.establishment))['remaining'],
            1 if report.status == 'COMPLETED' else 2,
        )
