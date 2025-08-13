release: python manage.py migrate --noinput && python manage.py 01_init_lookup_tables
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT --workers 3 --timeout 120
