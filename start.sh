#!/usr/bin/env bash
set -euo pipefail

# start.sh - usado por Render para desplegar la app
# Ejecuta migraciones, colecta archivos estáticos y arranca gunicorn.

# Si Render ya ejecutó pip install en el build step, no es necesario reinstalar.
# Mover db.sqlite3 del repo al disco persistente si existe (primer deploy)
if [ -f "./db.sqlite3" ] && [ ! -f "/opt/render/data/db.sqlite3" ]; then
  echo "[start.sh] Moviendo db.sqlite3 al disco persistente..."
  mkdir -p /opt/render/data
  mv ./db.sqlite3 /opt/render/data/db.sqlite3
fi

echo "[start.sh] Ejecutando migraciones..."
python manage.py migrate --noinput

echo "[start.sh] Ejecutando collectstatic..."
python manage.py collectstatic --noinput

echo "[start.sh] Arrancando gunicorn..."
# Bind al puerto que Render expone en $PORT
exec gunicorn config.wsgi --bind 0.0.0.0:${PORT:-8000} --workers 3 --log-file -
