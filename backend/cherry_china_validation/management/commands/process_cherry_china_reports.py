import time

from django.core.management.base import BaseCommand
from django.db.utils import OperationalError, ProgrammingError

from cherry_china_validation.worker import claim_next_report, process_report


class Command(BaseCommand):
    help = 'Procesa informes de cereza China encolados, usando Chromium de forma serial.'

    def add_arguments(self, parser):
        parser.add_argument('--once', action='store_true', help='Procesa un informe y termina.')
        parser.add_argument('--poll-interval', type=float, default=2.0)

    def handle(self, *args, **options):
        once = options['once']
        poll_interval = max(options['poll_interval'], 0.5)
        self.stdout.write(self.style.SUCCESS('Worker cereza China iniciado.'))
        while True:
            try:
                report_id = claim_next_report()
            except (OperationalError, ProgrammingError) as error:
                if once:
                    raise
                self.stderr.write(self.style.WARNING(f'Base de datos aún no lista: {type(error).__name__}'))
                time.sleep(poll_interval)
                continue
            if report_id is None:
                if once:
                    return
                time.sleep(poll_interval)
                continue

            report = process_report(report_id)
            self.stdout.write(f'Informe {report.pk}: {report.status}')
            if once:
                return