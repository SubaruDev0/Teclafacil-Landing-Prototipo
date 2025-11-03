from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from captcha.fields import CaptchaField

from apps.landing.models import Comment, ContactMessage


class CommentForm(forms.ModelForm):
    """
    Formulario basado en el modelo Comment para gestionar comentarios de noticias.
    """
    captcha = CaptchaField()

    class Meta:
        model = Comment
        fields = [
            'name',
            'email',
            'body',
        ]

        labels = {
            'name': _('Nombre completo'),
            'email': _('Correo electrónico'),
            'body': _('Comentario'),
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Tu nombre'),
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('tu@email.com'),
                'required': True,
            }),
            'body': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 4,
                'placeholder': _('Escribe tu comentario aquí...'),
                'required': True,
            }),
        }


class ContactForm(forms.ModelForm):
    """
    Formulario basado en el modelo ContactMessage para gestionar la entrada de datos de contacto.
    """
    captcha = CaptchaField()
    class Meta:
        model = ContactMessage
        fields = [
            'name',
            'email',
            'phone',
            'company',
            'subject',
            'message',
        ]
        labels = {
            'name': _('Nombre completo'),
            'email': _('Correo electrónico'),
            'phone': _('Teléfono'),
            'company': _('Empresa'),
            'subject': _('Asunto'),
            'message': _('Mensaje'),
        }

        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Tu nombre'),
                'required': True,
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('tu@email.com'),
                'required': True,
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('+56 9 1234 5678'),
                'required': True,
            }),
            'company': forms.TextInput(attrs={
                'class': 'form-control form-control-lg',
                'placeholder': _('Nombre de tu empresa'),
                'required': True,
            }),
            'subject': forms.Select(attrs={
                'class': 'form-select form-select-lg',
                'required': True,
            }),
            'message': forms.Textarea(attrs={
                'class': 'form-control form-control-lg',
                'rows': 5,
                'placeholder': _('Cuéntanos sobre tu proyecto o necesidad...'),
                'required': True,
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agregar opción por defecto al select
        self.fields['subject'].empty_label = _('Selecciona un tema')

    def clean_email(self):
        """
        Valida que el email proporcionado sea válido.
        """
        email = self.cleaned_data.get('email')

        try:
            validate_email(email)
        except ValidationError:
            raise ValidationError(_('Por favor ingrese un correo electrónico válido.'))

        return email

    def clean_phone(self):
        """
        Valida y limpia el número de teléfono.
        """
        phone = self.cleaned_data.get('phone')

        if phone:
            # Eliminar espacios y caracteres no numéricos comunes
            phone = phone.replace(' ', '').replace('-', '').replace('+', '')

            # Validar que solo contenga números después de limpiar
            if not phone.isdigit():
                raise ValidationError(_('El número de teléfono solo debe contener dígitos.'))

            # Validar longitud (ajustar según necesidades chilenas)
            if len(phone) < 8 or len(phone) > 12:
                raise ValidationError(_('El número de teléfono debe tener entre 8 y 12 dígitos.'))

        return phone

    def clean_message(self):
        """
        Valida que el mensaje tenga contenido sustancial.
        """
        message = self.cleaned_data.get('message')

        if message and len(message.strip()) < 10:
            raise ValidationError(_('Por favor proporcione más detalles en su mensaje.'))

        return message
