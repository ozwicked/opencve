#!/bin/sh
set -eu

# Watchtower can replace the stateless web image independently. Apply the
# idempotent Django preparation before accepting requests.
if [ "${OPENCVE_RUN_MIGRATIONS:-true}" = "true" ]; then
    python manage.py migrate --noinput
fi

if [ "${OPENCVE_COLLECT_STATIC:-true}" = "true" ]; then
    python manage.py collectstatic --noinput
fi

exec gunicorn opencve.wsgi "$@"
