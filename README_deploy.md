Deploy en Render (guía rápida)

Resumen
- Este proyecto es una landing en Django. Puedes desplegarlo en Render como un Web Service.
- Soporta dos opciones de base de datos:
  1) PostgreSQL (recomendado) mediante `DATABASE_URL` (Render Postgres managed service).
  2) SQLite en disco persistente de Render (útil para pruebas rápidas) usando `DJANGO_SQLITE_PATH=/opt/render/data/db.sqlite3`.

Archivos útiles
- `Procfile` — comando de inicio (gunicorn).
- `requirements.txt` — dependencias.
- `render.yaml` — ejemplo de blueprint para Render.
- `config/settings.py` — lee `DATABASE_URL`, `DJANGO_SQLITE_PATH`, `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.

Pasos (Postgres recomendado)
1) En tu repo, sube todos los cambios y haz push a GitHub/GitLab.
2) En Render, crea un nuevo Web Service (Connect a repo) y selecciona la rama.
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn config.wsgi --log-file -`
3) Crea un Managed Postgres y copia su `DATABASE_URL` en las env vars del servicio.
4) Configura variables de entorno en el servicio:
   - `DJANGO_SECRET_KEY` = (una cadena segura)
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `your-service-name.onrender.com` (o dejar en blanco para '*')
   - `DATABASE_URL` = (copiado desde Postgres service)
5) Opcional: activa `Connect a Database` y sincroniza.
6) En `Advanced` -> `Start Command`, puedes usar un pequeño script para ejecutar migraciones y collectstatic antes de arrancar Gunicorn. Por ejemplo:
   ```bash
   bash -lc "pip install -r requirements.txt && python manage.py migrate --noinput && python manage.py collectstatic --noinput && gunicorn config.wsgi --log-file -"
   ```
7) Despliega y abre la URL pública. Revisa logs en caso de errores (migrations, dependencias, etc.).

Pasos (SQLite en disco persistente de Render - pruebas rápidas)
1) Crea el servicio Web en Render.
2) En `Advanced` -> `Environment` configura `DJANGO_SQLITE_PATH` con `/opt/render/data/db.sqlite3`.
3) Asegúrate también de setear `DJANGO_SECRET_KEY` y `DJANGO_DEBUG=False`.
4) En `Advanced` -> `Start Command`, usa el mismo comando que arriba para ejecutar migraciones y collectstatic.
5) Importante: Render asigna un disco persistente si lo pides (disk size en `render.yaml`). Usa `/opt/render/data` como ruta.

Comandos útiles (localmente)
```bash
# instalar deps
pip install -r requirements.txt
# crear migraciones (si agregas modelos)
python manage.py makemigrations
python manage.py migrate
# colectar estáticos
python manage.py collectstatic --noinput
# correr servidor localmente
python manage.py runserver
```

Problemas comunes
- Error: psycopg2 no encontrado -> Asegúrate de `psycopg2-binary` en `requirements.txt`.
- Error 500 en producción -> revisar logs de Gunicorn y Django; verifica `ALLOWED_HOSTS`.
- Archivos estáticos no cargan -> asegurarse de `collectstatic` y que `STATIC_ROOT` exista; WhiteNoise está instalado.

Si quieres, puedo:
- Añadir un `start.sh` que ejecute install/migrate/collectstatic y arranque gunicorn.
- Crear un `Dockerfile` si prefieres desplegar vía Docker en Render.


