from django.contrib import admin
from .models import Reserva


@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'email', 'tipo', 'deposito', 'creado')
    list_filter = ('tipo', 'creado')
    search_fields = ('nombre', 'email')

