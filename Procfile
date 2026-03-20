web: python backend/manage.py migrate && gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:$PORT
