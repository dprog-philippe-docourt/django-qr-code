#!/bin/bash

echo APP_PORT=$APP_PORT
echo DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE

# Collect static files first.
python3 manage.py collectstatic --noinput


echo --- Start Gunicorn processes and replace the shell [i.e. invoke gunicorn with exec]
echo Starting Gunicorn.
exec gunicorn demo_site.wsgi:application \
    --name django-qr-code \
    --bind 0.0.0.0:$APP_PORT \
    --workers 2 \
    --worker-class=gthread \
    --log-level=info \
    --log-file=- \
    --access-logfile=- \
    --env DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE \
    "$@"
