from django.shortcuts import render, get_object_or_404
from django.utils.translation import get_language
from django.views import View
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import Http404
from apps.shop.models import Product, Category
from apps.shop.forms import CartAddProductForm
from apps.shop.cart import Cart


class ShopCatalogView(View):
    def get(self, request, *args, **kwargs):
        language = get_language()
        
        # Obtener todos los productos activos
        products = Product.objects.filter(is_active=True).select_related('category').prefetch_related('images')
        
        # Obtener todas las categorías activas con conteo de productos
        categories = Category.objects.filter(is_active=True).annotate(
            product_count=Count('products', filter=Q(products__is_active=True))
        ).order_by('order', 'pk')
        
        # Filtros
        selected_category = None
        category_id = request.GET.get('category')
        if category_id:
            try:
                selected_category = Category.objects.get(pk=category_id, is_active=True)
                products = products.filter(category=selected_category)
            except Category.DoesNotExist:
                pass
        
        # Filtro por tipo de producto
        product_type = request.GET.get('type')
        if product_type in ['PHYSICAL', 'COURSE', 'DIGITAL']:
            products = products.filter(product_type=product_type)
        
        # Filtro por rango de precio
        min_price = request.GET.get('min_price')
        max_price = request.GET.get('max_price')
        
        if min_price:
            try:
                products = products.filter(price__gte=float(min_price))
            except ValueError:
                pass
        
        if max_price:
            try:
                products = products.filter(price__lte=float(max_price))
            except ValueError:
                pass
        
        # Ordenamiento
        sort = request.GET.get('sort')
        if sort == 'price_asc':
            products = products.order_by('price')
        elif sort == 'price_desc':
            products = products.order_by('-price')
        elif sort == 'name':
            # Ordenar por nombre traducido
            products = products.order_by('translations__name')
        elif sort == 'newest':
            products = products.order_by('-created_at')
        else:
            # Orden por defecto: destacados primero, luego por orden y fecha
            products = products.order_by('-featured', 'order', '-created_at')
        
        # Obtener productos destacados para el banner
        featured_products = Product.objects.filter(
            is_active=True, 
            featured=True
        ).select_related('category')[:3]
        
        # Paginación
        paginator = Paginator(products, 12)  # 12 productos por página
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Construir URL canónica
        scheme = request.scheme
        host = request.get_host()
        path = request.path
        canonical_url = f"{scheme}://{host}{path}"
        
        context = {
            'canonical_url': canonical_url,
            'products': page_obj,
            'categories': categories,
            'selected_category': selected_category,
            'product_type': product_type,
            'min_price': min_price,
            'max_price': max_price,
            'sort': sort,
            'total_products': Product.objects.filter(is_active=True).count(),
            'featured_products': featured_products,
        }
        
        return render(request, 'frontend/shop_catalog.html', context)


class ProductDetailView(View):
    def get(self, request, slug, *args, **kwargs):
        language = get_language()
        
        # Obtener el producto por slug con todas las relaciones necesarias
        # Primero buscar en el idioma activo
        product = Product.objects.select_related('category').prefetch_related(
            'images', 'reviews__user'
        ).filter(
            translations__slug=slug,
            translations__language_code=language,  # Priorizar el idioma activo
            is_active=True
        ).first()
        
        # Si no se encuentra en el idioma activo, buscar en cualquier idioma
        if not product:
            product = Product.objects.select_related('category').prefetch_related(
                'images', 'reviews__user'
            ).filter(
                translations__slug=slug,
                is_active=True
            ).distinct().first()
        
        if not product:
            raise Http404("Producto no encontrado")
        
        # Asegurar que el producto se muestre en el idioma activo
        product.set_current_language(language, initialize=True)
        
        # Obtener productos relacionados (misma categoría)
        related_products = Product.objects.filter(
            category=product.category,
            is_active=True
        ).exclude(pk=product.pk).select_related('category').prefetch_related('images')[:4]
        
        # Contar productos por tipo para estadísticas adicionales
        from django.db.models import Count, Q
        category_stats = {}
        if product.category:
            category_stats = Product.objects.filter(
                category=product.category,
                is_active=True
            ).aggregate(
                physical_count=Count('pk', filter=Q(product_type='PHYSICAL')),
                course_count=Count('pk', filter=Q(product_type='COURSE')),
                digital_count=Count('pk', filter=Q(product_type='DIGITAL'))
            )
        
        # Crear formulario para agregar al carrito
        cart_form = CartAddProductForm(product=product)

        # Obtener el carrito para mostrar información
        cart = Cart(request)

        # Construir URL canónica
        scheme = request.scheme
        host = request.get_host()
        path = request.path
        canonical_url = f"{scheme}://{host}{path}"

        context = {
            'canonical_url': canonical_url,
            'product': product,
            'related_products': related_products,
            'category_stats': category_stats,
            'cart_form': cart_form,
            'cart': cart,
        }

        return render(request, 'frontend/product_detail.html', context)
