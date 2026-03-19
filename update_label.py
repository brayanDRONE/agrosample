import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from inspections.models import UserProfile

# Obtener el usuario 'dole'
user = User.objects.get(username='dole')
print(f"Usuario encontrado: {user.username}")

# Obtener o crear su profile
profile, created = UserProfile.objects.get_or_create(user=user)
print(f"Profile existía: {not created}")
print(f"Valor anterior: '{profile.sample_label_text}'")

# Actualizar al valor que definiste
profile.sample_label_text = "DOLE"
profile.save()

print(f"Valor actualizado a: '{profile.sample_label_text}'")
print("✓ Cambio guardado exitosamente")
