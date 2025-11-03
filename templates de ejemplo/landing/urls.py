from django.urls import path, include

from apps.landing import home_views, shop_views, news_views

app_name = 'landing'

urlpatterns = [
    path('', home_views.HomeView.as_view(), name='home'),
    path('shop/', shop_views.ShopCatalogView.as_view(), name='shop_catalog'),
    path('shop/product/<slug:slug>/', shop_views.ProductDetailView.as_view(), name='product_detail'),
    # Blog/Noticias
    path('news/', news_views.PostListView.as_view(), name='news_list'),
    path('news/<int:year>/<int:month>/<int:day>/<slug:post>/', news_views.PostDetailView.as_view(), name='news_detail'),
    path('news/tag/<slug:tag_slug>/', news_views.PostListView.as_view(), name='news_list_by_tag'),
    path('news/category/<slug:category_slug>/', news_views.PostListView.as_view(), name='news_list_by_category'),
    path('news/comment/ajax/', news_views.CommentAjaxView.as_view(), name='comment_ajax'),
    # Endpoint AJAX para refrescar captcha usado por el formulario de comentarios/contacto
    path('refresh-captcha/', news_views.refresh_captcha, name='refresh_captcha'),
]
