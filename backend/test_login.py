#!/usr/bin/env python
import os
import django


def main():
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
    django.setup()

    from django.contrib.auth.models import User

    u = User.objects.get(username='admin')
    print(f'Username: {u.username}')
    print(f'Is active: {u.is_active}')
    print(f'Is staff: {u.is_staff}')
    print(f'Is superuser: {u.is_superuser}')
    print(f'Password check (admin123): {u.check_password("admin123")}')
    if hasattr(u, 'profile'):
        print('Has profile: True')
        print(f'Role: {u.profile.role}')
    else:
        print('Has profile: False')


if __name__ == '__main__':
    main()
