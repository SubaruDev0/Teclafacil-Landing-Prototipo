# models.py
from django.conf import settings
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _, get_language, activate
from parler.managers import TranslatableManager
from parler.models import TranslatableModel, TranslatedFields
import pytz

from apps.account.models import User
from apps.core.mixins import TimestampedModel
from apps.core.utils import create_upload_handler


# Handler específico para imágenes de posts
def upload_to_posts(instance, filename):
    """Upload handler para imágenes de posts de noticias"""
    return create_upload_handler('posts')(instance, filename)


class Category(TimestampedModel):
    """Modelo para categorías de noticias"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'categoría'
        verbose_name_plural = 'categorías'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('landing:news_list_by_category', args=[self.slug])


class Tag(TimestampedModel):
    """Modelo para etiquetas de noticias"""
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'etiqueta'
        verbose_name_plural = 'etiquetas'

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('landing:news_list_by_tag', args=[self.slug])


class PublishedTranslatableManager(TranslatableManager):
    """
    Manager para obtener solo posts publicados, compatible con traducciones.
    """

    def get_queryset(self):
        return super().get_queryset().filter(status="PUBLISHED")


class Post(TranslatableModel, TimestampedModel):
    """Modelo para posts/noticias con soporte multiidioma"""
    STATUS_CHOICES = (
        ('DRAFT', _('Borrador')),
        ('PUBLISHED', _('Publicado')),
    )

    translations = TranslatedFields(
        title=models.CharField(max_length=250, blank=True),
        slug=models.SlugField(max_length=250, blank=True),
        body=models.TextField(blank=True),
        meta_description=models.CharField(
            max_length=160,
            blank=True,
            help_text="Meta descripción para SEO (máx. 160 caracteres). Se genera automáticamente si está vacío."
        )
    )

    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blog_posts')
    publish = models.DateTimeField(default=timezone.now)
    img_featured = models.FileField(upload_to=upload_to_posts, editable=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='DRAFT')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='posts')
    tags = models.ManyToManyField('Tag', related_name='posts', blank=True)

    # Campo para controlar la generación automática
    auto_generate_meta = models.BooleanField(
        default=True,
        help_text="Generar automáticamente meta descripciones con IA"
    )

    objects = TranslatableManager()
    published = PublishedTranslatableManager()

    class Meta:
        ordering = ('-publish',)
        verbose_name = 'noticia'
        verbose_name_plural = 'noticias'

    def __str__(self):
        return self.safe_translation_getter('title', any_language=True) or "Sin título"

    def get_absolute_url(self, lang=None):
        """
        Retorna la URL canónica del post.
        Si 'lang' se especifica, genera la URL para ese idioma.
        """
        # Guardar idioma actual para restaurar luego
        current_lang = get_language()

        try:
            if lang:
                # Activar temporalmente el idioma deseado
                activate(lang)

            # IMPORTANTE: Siempre usar la zona horaria de Chile para las URLs
            # Sin importar el timezone actual del request
            chile_tz = pytz.timezone('America/Santiago')

            # Convertir la fecha UTC a Chile timezone
            if timezone.is_aware(self.publish):
                # Si ya es aware, convertir directamente
                localized_publish = self.publish.astimezone(chile_tz)
            else:
                # Si es naive, asumir UTC y luego convertir
                utc_publish = pytz.UTC.localize(self.publish)
                localized_publish = utc_publish.astimezone(chile_tz)

            # Obtener el slug en el idioma actual
            slug = self.safe_translation_getter('slug')
            if not slug:
                # Si no hay slug en este idioma, usar cualquier slug disponible
                slug = self.safe_translation_getter('slug', any_language=True) or "no-slug"

            return reverse('landing:news_detail', args=[
                localized_publish.year,
                localized_publish.month,
                localized_publish.day,
                slug
            ])
        finally:
            if lang and current_lang:
                activate(current_lang)

    def save(self, *args, **kwargs):
        """
        Guarda Post asegurando que cada idioma con título tenga su slug.
        """
        creating = not self.pk
        current_lang = get_language()

        # Guardar primero el objeto base
        super().save(*args, **kwargs)

        try:
            # Solo si ya tenemos instancia (ID)
            for lang_code, _ in settings.LANGUAGES:
                try:
                    self.set_current_language(lang_code)

                    if self.has_translation(lang_code):
                        title = self.safe_translation_getter('title', any_language=False)
                        slug = self.safe_translation_getter('slug', any_language=False)

                        if title and not slug:
                            generated_slug = self._generate_unique_slug(lang_code, title)
                            self.slug = generated_slug
                            self.save_translations()
                except Exception as e:
                    print(f"[Save Warning] No se pudo generar slug para idioma {lang_code}: {e}")

        finally:
            activate(current_lang)

    def _generate_unique_slug(self, lang_code, title):
        """Genera un slug único en un idioma."""
        from parler.managers import TranslatableQuerySet

        base_slug = slugify(title)
        unique_slug = base_slug
        num = 1

        qs = Post.objects.all()
        if isinstance(qs, TranslatableQuerySet):
            qs = qs.translated(lang_code)

        qs = qs.exclude(pk=self.pk)

        while qs.filter(translations__slug=unique_slug).exists():
            unique_slug = f"{base_slug}-{num}"
            num += 1

        return unique_slug

    def get_meta_description(self, lang=None):
        """
        Obtiene la meta descripción en el idioma especificado.
        Si no existe, retorna una versión truncada del body.
        """
        current_lang = None
        if lang:
            current_lang = get_language()
            activate(lang)

        try:
            meta_desc = self.safe_translation_getter('meta_description')
            if meta_desc:
                return meta_desc

            # Fallback: usar el body truncado
            body = self.safe_translation_getter('body')
            if body:
                from django.utils.html import strip_tags
                clean_body = strip_tags(body).strip()
                return clean_body[:157] + "..." if len(clean_body) > 157 else clean_body

            return ""
        finally:
            if lang and current_lang:
                activate(current_lang)

    def has_translation_safe(self, language_code):
        """
        Verifica si existe una traducción de forma segura
        """
        try:
            # Usar safe_translation_getter - si retorna None, no existe la traducción
            title = self.safe_translation_getter('title', language_code=language_code, default=None)
            return title is not None
        except:
            return False

    def get_translation_safe(self, language_code):
        """
        Obtiene una traducción de forma segura
        """
        try:
            # Verificar primero si existe
            if not self.has_translation_safe(language_code):
                return None

            # Obtener todos los campos
            return {
                'title': self.safe_translation_getter('title', language_code=language_code, default=''),
                'body': self.safe_translation_getter('body', language_code=language_code, default=''),
                'slug': self.safe_translation_getter('slug', language_code=language_code, default=''),
                'meta_description': self.safe_translation_getter('meta_description', language_code=language_code,
                                                                 default='')
            }
        except:
            return None

    def get_all_translations_dict(self):
        """
        Obtiene todas las traducciones disponibles
        """
        translations = {}

        for lang_code, _ in settings.LANGUAGES:
            trans_data = self.get_translation_safe(lang_code)
            if trans_data:
                translations[lang_code] = trans_data

        return translations

    @property
    def available_languages(self):
        """
        Retorna lista de códigos de idioma que tienen traducciones
        """
        languages = []
        for lang_code, _ in settings.LANGUAGES:
            if self.has_translation_safe(lang_code):
                languages.append(lang_code)
        return languages

    def clear_translation_cache(self):
        """
        Limpia cualquier cache de traducción de forma segura
        """
        # Solo intentar limpiar si el atributo existe
        if hasattr(self, '_translations_cache'):
            try:
                delattr(self, '_translations_cache')
            except:
                pass

        # Forzar refresco desde DB si es posible
        try:
            self.refresh_from_db()
        except:
            pass


class Comment(TimestampedModel):
    """Modelo para comentarios en posts/noticias"""
    # el related_name permite sobrescribir el object name en la relacion ej. post.comments.all().
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    name = models.CharField(max_length=50)
    email = models.EmailField()
    body = models.TextField()
    active = models.BooleanField(default=False)

    class Meta:
        ordering = ('-created_at',)
        verbose_name = 'comentario'
        verbose_name_plural = 'comentarios'

    def __str__(self):
        return f'Comentario de {self.name} en {self.post}'


class ContactMessage(TimestampedModel):
    """Modelo para mensajes de contacto"""
    SUBJECT_CHOICES = [
        ('support', _('Soporte técnico')),
        ('project', _('Nuevo proyecto')),
        ('quote', _('Cotización')),
        ('other', _('Otro')),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True, null=True)
    company = models.CharField(max_length=150, blank=True, null=True)
    subject = models.CharField(max_length=50, choices=SUBJECT_CHOICES)
    message = models.TextField()

    class Meta:
        verbose_name = _('Mensaje de contacto')
        verbose_name_plural = _('Mensajes de contacto')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.subject}"


# Helper para invalidar cache de detalle de post cuando cambian comentarios
def invalidate_post_detail_cache(post):
    """
    Elimina las keys de cache relacionadas con el detalle del post para todos los idiomas
    y cualquier cache de comentarios por post.
    """
    try:
        from django.core.cache import cache
        import pytz
        from django.utils import timezone
        from django.conf import settings as djsettings

        chile_tz = pytz.timezone('America/Santiago')

        # Asegurar que publish sea aware y en zona Chile
        publish_dt = post.publish
        if timezone.is_naive(publish_dt):
            publish_dt = pytz.UTC.localize(publish_dt)
        localized = publish_dt.astimezone(chile_tz)

        year = localized.year
        month = localized.month
        day = localized.day

        # Intentar obtener slugs por idioma y borrar la cache correspondiente
        for lang_code, _ in djsettings.LANGUAGES:
            try:
                slug = post.safe_translation_getter('slug', language_code=lang_code, default=None)
                if not slug:
                    # intentar obtener cualquier slug disponible para ese idioma
                    continue
                cache_key = f'post_detail_{year}_{month}_{day}_{slug}_{lang_code}'
                cache.delete(cache_key)
            except Exception:
                # No detener el proceso por errores al borrar una key
                continue

        # Borrar cache de comentarios por post si existe
        try:
            cache.delete(f'post_comments_{post.pk}')
        except Exception:
            pass

    except Exception:
        # No lanzar errores en producción por fallos de cache
        pass


# Señales para invalidar cache cuando un comentario se guarda o elimina
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


@receiver(post_save, sender=Comment)
def comment_saved(sender, instance, created, **kwargs):
    """
    Cuando se guarda un comentario, invalidar la cache del detalle del post
    para que la lista de comentarios se refresque cuando sea aprobado.
    """
    try:
        invalidate_post_detail_cache(instance.post)
    except Exception:
        pass


@receiver(post_delete, sender=Comment)
def comment_deleted(sender, instance, **kwargs):
    """
    Cuando se elimina un comentario, invalidar la cache del detalle del post.
    """
    try:
        invalidate_post_detail_cache(instance.post)
    except Exception:
        pass


@receiver(post_save, sender=Post)
def post_saved(sender, instance, created, **kwargs):
    """
    Cuando se guarda un Post, limpiar caches relacionadas (detalle, listas, categorías, tags).
    """
    try:
        # Invalidar cache del detalle para todas las traducciones
        invalidate_post_detail_cache(instance)

        # Invalidar keys generales de listados que dependan de idioma
        from django.core.cache import cache
        for lang_code, _ in settings.LANGUAGES:
            cache.delete(f'all_categories_{lang_code}')
            cache.delete(f'all_tags_{lang_code}')
            cache.delete(f'popular_tags_{lang_code}')

        # Opcional: limpiar keys de listados (la manera simple: borrar todo prefijo 'queryset_post_list')
        # Nota: no todos los backends de cache soportan iteración de keys, así que esto es un intento seguro
    except Exception:
        pass


@receiver(post_delete, sender=Post)
def post_deleted(sender, instance, **kwargs):
    """
    Cuando se elimina un Post, invalidar caches relacionadas.
    """
    try:
        invalidate_post_detail_cache(instance)
    except Exception:
        pass


