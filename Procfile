release: python manage.py migrate --noinput
web: gunicorn electoral_office.wsgi --log-file - --log-level debug --timeout 120 --bind 0.0.0.0:$PORT
