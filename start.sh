#!/usr/bin/env bash
set -euo pipefail

# start.sh - usado por Render para desplegar la app
# Ejecuta migraciones, colecta archivos estáticos y arranca gunicorn.

# Si Render ya ejecutó pip install en el build step, no es necesario reinstalar.
# Pero no hacemos pip install aquí para mantener el start rápido.

echo "[start.sh] Ejecutando migraciones..."
python manage.py migrate --noinput

echo "[start.sh] Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo "[start.sh] Arrancando gunicorn..."
# Bind al puerto que Render expone en $PORT
exec gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 3 --log-file -

