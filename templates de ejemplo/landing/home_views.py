from django.shortcuts import render
from django.utils.translation import get_language
from django.views import View
from django.db.models import Q
from apps.shop.models import Product, Category


class HomeView(View):
    def get(self, request, *args, **kwargs):
        language = get_language()  # obtiene el idioma activo del usuario

        # Obtener el host y esquema
        scheme = self.request.scheme
        host = self.request.get_host()

        # Obtener la ruta actual EXACTA (preservando el idioma)
        path = self.request.path

        # Construir la URL base correctamente
        base_url = f"{scheme}://{host}{path}"

        # Iniciar con la URL base como canónica
        canonical_url = base_url

        # Obtener cursos destacados (máximo 4)
        featured_courses = Product.objects.filter(
            product_type='COURSE',
            is_active=True,
            featured=True
        ).select_related('category').prefetch_related('images')[:4]
        
        # Si no hay cursos destacados, obtener los más recientes
        if not featured_courses:
            featured_courses = Product.objects.filter(
                product_type='COURSE',
                is_active=True
            ).select_related('category').prefetch_related('images').order_by('-created_at')[:4]
        
        # Obtener productos físicos destacados (dispositivos, máximo 4)
        featured_devices = Product.objects.filter(
            product_type='PHYSICAL',
            is_active=True,
            featured=True
        ).select_related('category').prefetch_related('images')[:4]
        
        # Si no hay dispositivos destacados, obtener los más recientes
        if not featured_devices:
            featured_devices = Product.objects.filter(
                product_type='PHYSICAL',
                is_active=True
            ).select_related('category').prefetch_related('images').order_by('-created_at')[:4]
        
        # Obtener productos digitales destacados (si hay)
        featured_digital = Product.objects.filter(
            product_type='DIGITAL',
            is_active=True,
            featured=True
        ).select_related('category').prefetch_related('images')[:4]
        
        # Estadísticas generales
        total_courses = Product.objects.filter(
            product_type='COURSE',
            is_active=True
        ).count()
        
        total_devices = Product.objects.filter(
            product_type='PHYSICAL',
            is_active=True
        ).count()
        
        # Obtener categorías activas para mostrar en el menú si es necesario
        active_categories = Category.objects.filter(
            is_active=True,
            products__is_active=True
        ).distinct().order_by('order')[:6]

        context = {
            'canonical_url': canonical_url,
            'featured_courses': featured_courses,
            'featured_devices': featured_devices,
            'featured_digital': featured_digital,
            'total_courses': total_courses,
            'total_devices': total_devices,
            'active_categories': active_categories,
        }

        return render(request, 'frontend/home.html', context)
