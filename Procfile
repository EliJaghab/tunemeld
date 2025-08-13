release: python manage.py migrate --noinput && python manage.py populate_lookup_tables
web: gunicorn core.wsgi:application --bind 0.0.0.0:$PORT
