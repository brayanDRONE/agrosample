from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from inspections.models import UserProfile


class Command(BaseCommand):
    help = 'Asigna el perfil SUPERADMIN a un superusuario existente.'

    def add_arguments(self, parser):
        parser.add_argument('username')

    def handle(self, *args, **options):
        try:
            user = User.objects.get(username=options['username'], is_superuser=True, is_active=True)
        except User.DoesNotExist as exc:
            raise CommandError('El usuario debe ser un superusuario activo existente.') from exc
        if not user.has_usable_password():
            raise CommandError('El superusuario debe tener una contraseña utilizable.')
        UserProfile.objects.update_or_create(user=user, defaults={'role': 'SUPERADMIN'})
        self.stdout.write(self.style.SUCCESS('Perfil SUPERADMIN configurado.'))
