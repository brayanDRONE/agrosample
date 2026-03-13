from django.db import migrations
from django.contrib.auth.hashers import make_password


def create_superuser(apps, schema_editor):
    """Crea un superusuario por defecto si no existe"""
    User = apps.get_model('auth', 'User')
    UserProfile = apps.get_model('inspections', 'UserProfile')
    
    if not User.objects.filter(username='admin').exists():
        # Crear superusuario
        admin_user = User.objects.create(
            username='admin',
            email='admin@usda.cl',
            is_superuser=True,
            is_staff=True
        )
        admin_user.password = make_password('admin123')
        admin_user.save()
        
        # Crear perfil con rol SUPERADMIN
        UserProfile.objects.create(
            user=admin_user,
            role='SUPERADMIN'
        )
        
        print("OK: Superusuario 'admin' y perfil SUPERADMIN creados exitosamente")
    else:
        # Si el usuario ya existe, verificar que tenga perfil
        admin_user = User.objects.get(username='admin')
        if not UserProfile.objects.filter(user=admin_user).exists():
            UserProfile.objects.create(
                user=admin_user,
                role='SUPERADMIN'
            )
            print("OK: Perfil SUPERADMIN creado para usuario 'admin' existente")
        else:
            print("INFO: Superusuario 'admin' y perfil ya existen")


class Migration(migrations.Migration):

    dependencies = [
        ('inspections', '0010_samplingresult_incremento_aplicado_and_more'),
    ]

    operations = [
        migrations.RunPython(create_superuser),
    ]
