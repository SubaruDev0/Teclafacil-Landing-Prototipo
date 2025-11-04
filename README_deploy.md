Deploy rápido en Render (SQLite prototipo)

1) En Render > Service Settings:
- Build Command: pip install -r requirements.txt
- Start Command: ./start.sh
- Attach 1 GB persistent disk

2) Environment variables:
- DJANGO_SECRET_KEY = '(^#6_2pwdmez(xu(4erb-rpt8fdkx%#pl4ui_f91wm7h)tk2&7
'
- DJANGO_DEBUG = True
- DJANGO_ALLOWED_HOSTS = teclafacil-landing-prototipo-3.onrender.com
- DJANGO_SQLITE_PATH = /opt/render/data/db.sqlite3

3) Si quieres los datos locales: git add db.sqlite3 && git commit -m "add sqlite" && git push
(El start.sh moverá db.sqlite3 al disco persistente en el primer deploy)

4) Manual Deploy -> Deploy latest commit
5) Logs: ver pasos migrate, collectstatic y gunicorn

Hecho.
