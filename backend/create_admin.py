from django.contrib.auth.models import User
from inspections.models import UserProfile

# Crear o actualizar usuario admin
user, created = User.objects.get_or_create(
    username='admin',
    defaults={
        'email': 'admin@agrosample.cl',
        'first_name': 'Administrador',
        'last_name': 'Sistema',
        'is_staff': True,
        'is_superuser': True
    }
)

# Establecer contraseña
user.set_password('admin')
user.save()

# Crear o actualizar perfil
profile, profile_created = UserProfile.objects.get_or_create(
    user=user,
    defaults={'role': 'SUPERADMIN'}
)

if created:
    print("✓ Usuario admin creado exitosamente")
else:
    print("✓ Usuario admin actualizado exitosamente")

print(f"  Usuario: admin")
print(f"  Contraseña: admin")
print(f"  Rol: SUPERADMIN")
