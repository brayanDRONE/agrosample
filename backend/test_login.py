#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User
from inspections.models import UserProfile

# Verificar usuario admin
u = User.objects.get(username='admin')
print(f'Username: {u.username}')
print(f'Is active: {u.is_active}')
print(f'Is staff: {u.is_staff}')
print(f'Is superuser: {u.is_superuser}')
print(f'Password check (admin123): {u.check_password("admin123")}')

# Verificar perfil
if hasattr(u, 'profile'):
    print(f'Has profile: True')
    print(f'Role: {u.profile.role}')
else:
    print(f'Has profile: False')
