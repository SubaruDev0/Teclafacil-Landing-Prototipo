from django.shortcuts import render, redirect
from django.urls import reverse
from .forms import ReservaForm
from .models import Reserva, Feedback


def home(request):
    # calcular métricas
    reservas_count = Reserva.objects.count()
    empresas_count = Reserva.objects.filter(tipo='pilot').count()
    feedbacks = Feedback.objects.all()
    satisfaccion = 0
    if feedbacks.exists():
        avg_rating = sum(f.rating for f in feedbacks) / feedbacks.count()
        satisfaccion = round(avg_rating * 20)  # convertir 1-5 a porcentaje 20-100

    # si llega email desde CTA (GET), lo mostramos en el enlace a reservar
    cta_email = request.GET.get('email', '')

    # testimonios publicados (rating >=4)
    published_feedbacks = Feedback.objects.filter(rating__gte=4).order_by('-creado')[:6]

    context = {
        'reservas_count': reservas_count,
        'empresas_count': empresas_count,
        'satisfaccion': satisfaccion,
        'cta_email': cta_email,
        'published_feedbacks': published_feedbacks,
        'fb_error': request.GET.get('fb_error', ''),
    }
    return render(request, 'landing/home.html', context)


def reservar(request):
    # aceptar prefill via GET
    if request.method == 'POST':
        form = ReservaForm(request.POST)
        if form.is_valid():
            reserva = form.save(commit=False)
            # establecer deposito según tipo
            tipo = reserva.tipo
            # precios del producto
            if tipo == 'teclado':
                precio = 50000.00
                reserva.deposito = precio  # 100% reembolsable
            elif tipo == 'kit':
                precio = 80000.00
                reserva.deposito = precio  # 100% reembolsable
            elif tipo == 'pilot':
                precio = 200000.00
                reserva.deposito = 0.00  # empresas no pagan depósito
            else:
                precio = 50000.00
                reserva.deposito = precio
            reserva.save()
            return redirect(reverse('landing:gracias'))
    else:
        initial = {}
        email = request.GET.get('email')
        tipo = request.GET.get('tipo')
        if email:
            initial['email'] = email
        if tipo:
            initial['tipo'] = tipo
        form = ReservaForm(initial=initial)
    # calcular valores iniciales para mostrar en la plantilla
    tipo_effective = request.GET.get('tipo') or (form.initial.get('tipo') if hasattr(form, 'initial') else None) or 'kit'
    if tipo_effective == 'teclado':
        initial_product_price = 'CLP $50.000'
        initial_deposit = 'CLP $50.000'
    elif tipo_effective == 'kit':
        initial_product_price = 'CLP $80.000'
        initial_deposit = 'CLP $80.000'
    elif tipo_effective == 'pilot':
        initial_product_price = 'CLP $200.000'
        initial_deposit = 'CLP $0'
    else:
        initial_product_price = 'CLP $50.000'
        initial_deposit = 'CLP $50.000'
    return render(request, 'landing/reservar.html', {'form': form, 'request': request, 'initial_product_price': initial_product_price, 'initial_deposit': initial_deposit})


def gracias(request):
    return render(request, 'landing/gracias.html')


def empresas(request):
    return render(request, 'landing/empresas.html')


def feedback(request):
    if request.method == 'POST':
        # pequeño formulario manual sin ModelForm
        nombre = request.POST.get('nombre', '').strip()
        email = request.POST.get('email', '')
        rating = int(request.POST.get('rating', 0) or 0)
        comentario = request.POST.get('comentario', '')
        # nombre obligatorio para publicar feedback
        if not nombre:
            return redirect(reverse('landing:home') + '?fb_error=1')
        if rating and 1 <= rating <= 5:
            Feedback.objects.create(nombre=nombre, email=email, rating=rating, comentario=comentario)
    return redirect(reverse('landing:home'))
