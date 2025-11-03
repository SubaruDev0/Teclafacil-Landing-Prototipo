# apps/landing/templatetags/blog_extras.py
from django import template
from django.db.models import Count, Q
from django.utils.html import strip_tags
from django.utils.translation import get_language
from django.utils.safestring import mark_safe
from django.core.cache import cache
from django.conf import settings
import re
import markdown
import html

register = template.Library()


# Mantener los tags existentes
@register.simple_tag
def total_posts():
    # Importar localmente para evitar errores al cargar el módulo de templatetags
    from ..models import Post
    return Post.objects.all().count()


@register.inclusion_tag('snippets/news/latest_posts.html')
def show_latest_posts(count=5):
    from ..models import Post
    current_lang = get_language()
    latest_posts = (
        Post.published
        .translated(current_lang)
        .select_related('author', 'category')
        .prefetch_related('tags')
        .order_by('-publish')[:count]
    )
    return {'latest_posts': latest_posts}


@register.inclusion_tag('snippets/news/last-news.html')
def show_latest_posts_home(count=3):
    from ..models import Post
    latest_posts = (
        Post.objects.all()
        .filter(status='PUBLISHED')
        .select_related('author', 'category')
        .prefetch_related('tags', 'translations')
        .order_by('-publish')[:count]
    )
    return {'latest_posts': latest_posts}


@register.simple_tag
def get_most_commented_posts(count=5):
    from ..models import Post
    return (
        Post.objects.all()
        .filter(status='PUBLISHED')
        .select_related('author', 'category')
        .prefetch_related('tags')
        .annotate(total_comments=Count('comments'))
        .order_by('-total_comments')[:count]
    )


@register.filter(name='markdown')
def markdown_format(text):
    return mark_safe(markdown.markdown(text))


@register.filter
def strip_tags_and_entities(value):
    return html.unescape(strip_tags(value))


@register.simple_tag
def post_link_url(post):
    """
    Devuelve la URL del post con el idioma correcto,
    limpiando prefijos de idioma si es necesario.
    """
    current_lang = get_language()
    available_langs = post.available_languages  # Usar la propiedad

    # Determinar idioma a usar
    if current_lang in available_langs:
        lang = current_lang
    else:
        lang = 'es'  # fallback a español

    # Generar la URL normal
    url = post.get_absolute_url(lang=lang)

    # Si se está usando i18n_patterns, el URL ya puede tener un idioma
    if settings.USE_I18N:
        # Eliminar cualquier prefijo de idioma en la URL
        regex = r'^/(%s)/' % '|'.join(re.escape(lang_code) for lang_code, _ in settings.LANGUAGES)
        url = re.sub(regex, '/', url)

        # Ahora anteponer correctamente
        return f"/{lang}{url}"
    else:
        return url


# NUEVOS TEMPLATE TAGS PARA EL TEMPLATE news.html

@register.simple_tag
def get_categories_with_count():
    """
    Obtiene todas las categorías con el conteo de posts publicados
    """
    from ..models import Category
    current_lang = get_language()
    cache_key = f'categories_with_count_{current_lang}'

    categories = cache.get(cache_key)
    if categories is None:
        # Contar posts publicados independientemente de si tienen traducción en el idioma activo
        categories = Category.objects.annotate(
            post_count=Count(
                'posts',
                filter=Q(
                    posts__status='PUBLISHED'
                ),
                distinct=True
            )
        ).filter(post_count__gt=0).order_by('-post_count')
        cache.set(cache_key, list(categories), 60 * 60 * 2)  # Cache por 2 horas

    return categories


@register.simple_tag
def get_popular_tags(count=15):
    """
    Obtiene los tags más populares
    """
    from ..models import Tag
    current_lang = get_language()
    cache_key = f'popular_tags_{current_lang}_{count}'

    tags = cache.get(cache_key)
    if tags is None:
        # Contar posts publicados independientemente de traducciones para mostrar tags en todos los idiomas
        tags = Tag.objects.annotate(
            post_count=Count(
                'posts',
                filter=Q(
                    posts__status='PUBLISHED'
                ),
                distinct=True
            )
        ).filter(post_count__gt=0).order_by('-post_count')[:count]
        cache.set(cache_key, list(tags), 60 * 60 * 2)  # Cache por 2 horas

    return tags


@register.filter
def get_excerpt(post, word_count=30):
    """
    Obtiene un extracto del post limpiando HTML y entidades de forma más completa
    """
    body = post.safe_translation_getter('body', default='')
    if body:
        import re

        # Si el contenido empieza con una lista, intentar extraer el primer párrafo después de la lista
        # o convertir los elementos de la lista en texto plano
        if body.strip().startswith(('<ul', '<ol', '<li')):
            # Buscar el primer párrafo después de las listas
            paragraph_match = re.search(r'</[uo]l>\s*<p[^>]*>(.*?)</p>', body, re.IGNORECASE | re.DOTALL)
            if paragraph_match:
                # Usar el primer párrafo después de la lista
                body = paragraph_match.group(1)
            else:
                # Si no hay párrafo después, convertir los elementos de lista en texto
                # Reemplazar elementos de lista con guiones
                body = re.sub(r'<li[^>]*>', '• ', body, flags=re.IGNORECASE)
                body = re.sub(r'</li>', '. ', body, flags=re.IGNORECASE)
                body = re.sub(r'</?[uo]l[^>]*>', '', body, flags=re.IGNORECASE)

        # Eliminar todos los tags HTML
        clean_body = strip_tags(body)

        # Decodificar entidades HTML múltiples veces (por si hay entidades anidadas)
        for _ in range(3):
            decoded = html.unescape(clean_body)
            if decoded == clean_body:
                break
            clean_body = decoded

        # Eliminar caracteres especiales no deseados
        clean_body = clean_body.replace('\xa0', ' ')  # Non-breaking space
        clean_body = clean_body.replace('\u200b', '')  # Zero-width space
        clean_body = clean_body.replace('\r', ' ')  # Carriage return
        clean_body = clean_body.replace('\n', ' ')  # New line
        clean_body = clean_body.replace('\t', ' ')  # Tab
        clean_body = clean_body.replace('•', '')  # Bullet points
        clean_body = clean_body.replace('·', '')  # Middle dot
        clean_body = clean_body.replace('■', '')  # Square bullet
        clean_body = clean_body.replace('▪', '')  # Small square bullet
        clean_body = clean_body.replace('◦', '')  # White bullet
        clean_body = clean_body.replace('‣', '')  # Triangle bullet
        clean_body = clean_body.replace('⁃', '')  # Hyphen bullet

        # Eliminar múltiples puntos consecutivos
        clean_body = re.sub(r'\.{2,}', '. ', clean_body)

        # Eliminar espacios múltiples y limpiar
        clean_body = ' '.join(clean_body.split())
        clean_body = clean_body.strip()

        # Si el texto empieza con punto o coma, eliminarlo
        if clean_body and clean_body[0] in '.,;:':
            clean_body = clean_body[1:].strip()

        # Cortar por palabras
        words = clean_body.split()
        if len(words) > word_count:
            excerpt = ' '.join(words[:word_count])
            # Asegurar que no termine en puntuación incompleta
            if excerpt and excerpt[-1] in '.,;:':
                excerpt = excerpt[:-1]
            return excerpt + '...'
        return clean_body
    return ''


@register.simple_tag
def build_query_string(request, **kwargs):
    """
    Construye una query string manteniendo los parámetros existentes
    y actualizando con los nuevos valores
    """
    query_dict = request.GET.copy()

    for key, value in kwargs.items():
        if value is None:
            query_dict.pop(key, None)
        else:
            query_dict[key] = value

    return query_dict.urlencode()


@register.simple_tag
def get_post_image_url(post):
    """
    Obtiene la URL de la imagen del post de forma segura
    """
    if post.img_featured:
        return post.img_featured.url
    return None


@register.filter
def highlight_search(text, search_query):
    """
    Resalta el texto de búsqueda en el contenido
    """
    if not search_query or not text:
        return text

    # Escapar caracteres especiales de regex
    escaped_query = re.escape(search_query)
    pattern = re.compile(f'({escaped_query})', re.IGNORECASE)

    # Reemplazar con span destacado
    highlighted = pattern.sub(
        r'<span class="search-highlight">\1</span>',
        str(text)
    )

    return mark_safe(highlighted)
