from django.urls import path
from . import views

app_name = 'landing'

urlpatterns = [
    path('', views.home, name='home'),
    path('reservar/', views.reservar, name='reservar'),
    path('gracias/', views.gracias, name='gracias'),
    path('empresas/', views.empresas, name='empresas'),
    path('feedback/', views.feedback, name='feedback'),
]
