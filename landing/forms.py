from django import forms
from .models import Reserva


class ReservaForm(forms.ModelForm):
    class Meta:
        model = Reserva
        fields = ['nombre', 'email', 'telefono', 'tipo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Tu nombre'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'correo@ejemplo.com'}),
            'telefono': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Opcional'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # etiquetas claras
        self.fields['nombre'].label = 'Nombre'
        self.fields['email'].label = 'Email'
        self.fields['telefono'].label = 'Telefono'
        self.fields['tipo'].label = 'Tipo de compra'
