from django.contrib import admin
from parler.admin import TranslatableAdmin
from .models import Post, Category, Tag, Comment, invalidate_post_detail_cache
from django import forms
from parler.forms import TranslatableModelForm


# ======================
# CATEGORY ADMIN
# ======================
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'post_count', 'created_at')
    search_fields = ('name',)

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Cantidad de posts'


# ======================
# TAG ADMIN
# ======================
@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    prepopulated_fields = {'slug': ('name',)}
    list_display = ('name', 'slug', 'post_count', 'created_at')
    search_fields = ('name',)

    def post_count(self, obj):
        return obj.posts.count()
    post_count.short_description = 'Cantidad de posts'


# ======================
# POST ADMIN
# ======================

class PostAdminForm(TranslatableModelForm):
    """Formulario personalizado para campos traducibles.
    Reemplazamos CKEditor por un textarea que será inicializado con Quill (CDN)
    mediante un script cargado en la sección Media del formulario/admin.
    """
    body = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'quill-input', 'rows': 10}),
        required=False,
    )

    class Media:
        css = {
            'all': (
                'https://cdn.quilljs.com/1.3.6/quill.snow.css',
            )
        }
        js = (
            'https://cdn.quilljs.com/1.3.6/quill.min.js',
        )

    class Meta:
        model = Post
        fields = '__all__'


@admin.register(Post)
class PostAdmin(TranslatableAdmin):
    form = PostAdminForm

    list_display = ('get_title', 'author', 'category', 'status', 'publish', 'created_at')
    # Usamos DateFieldListFilter para fecha (permitiendo filtrar por año/mes)
    list_filter = ('status', 'category', ('publish', admin.DateFieldListFilter), 'created_at')
    search_fields = ('translations__title', 'translations__body')
    filter_horizontal = ('tags',)

    # Fieldsets organizados según los requisitos. Los campos traducibles (title, slug, body,
    # meta_description) se incluyen en un fieldset específico; Parler los mostrará en pestañas
    # por idioma automáticamente.
    fieldsets = (
        ('Información General', {
            'fields': ('author', 'category', 'status', 'tags')
        }),
        ('Contenido Traducible', {
            'fields': ('title', 'slug', 'body', 'meta_description'),
            'description': 'Campos traducibles: utilice las pestañas de idioma para cada traducción.'
        }),
        ('Multimedia', {
            'fields': ('img_featured',)
        }),
        ('Configuración SEO', {
            'fields': ('auto_generate_meta',),
            'classes': ('collapse',)
        }),
        ('Publicación', {
            'fields': ('publish',)
        }),
    )

    def get_title(self, obj):
        return obj.safe_translation_getter('title', any_language=True) or "Sin título"
    get_title.short_description = 'Título'


# ======================
# COMMENT ADMIN
# ======================
@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'post_title_truncated', 'active', 'created_at')
    list_filter = ('active', 'created_at')
    search_fields = ('name', 'email', 'body', 'post__translations__title')
    readonly_fields = ('created_at', 'updated_at')
    actions = ['approve_comments', 'reject_comments']

    def post_title_truncated(self, obj):
        title = obj.post.safe_translation_getter('title', any_language=True)
        return title[:50] + '...' if title and len(title) > 50 else title or "Sin título"
    post_title_truncated.short_description = 'Post'

    @admin.action(description='Aprobar comentarios seleccionados')
    def approve_comments(self, request, queryset):
        # Guardar los posts afectados antes de actualizar (update no lanza signals)
        post_ids = list(queryset.values_list('post_id', flat=True).distinct())
        queryset.update(active=True)
        # Invalidar cache para cada post
        for pid in post_ids:
            try:
                post = Post.objects.get(pk=pid)
                invalidate_post_detail_cache(post)
            except Post.DoesNotExist:
                continue

    @admin.action(description='Rechazar comentarios seleccionados')
    def reject_comments(self, request, queryset):
        post_ids = list(queryset.values_list('post_id', flat=True).distinct())
        queryset.update(active=False)
        for pid in post_ids:
            try:
                post = Post.objects.get(pk=pid)
                invalidate_post_detail_cache(post)
            except Post.DoesNotExist:
                continue
