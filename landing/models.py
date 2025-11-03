from django.db import models


class Reserva(models.Model):
    NOMBRE_MAX = 120

    TIPOS = (
        ('teclado', 'TeclaFácil (solo)'),
        ('kit', 'TeclaFácil + mouse + audífonos (Kit Profesional)'),
        ('pilot', 'Programa Piloto (Empresa)'),
    )

    nombre = models.CharField(max_length=NOMBRE_MAX)
    email = models.EmailField()
    tipo = models.CharField(max_length=50, choices=TIPOS, default='kit')
    telefono = models.CharField(max_length=30, blank=True)
    deposito = models.DecimalField(max_digits=10, decimal_places=2, default=50000.00)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nombre} <{self.email}> - {self.tipo}"

    def save(self, *args, **kwargs):
        # asegurar depósito consistente según tipo al guardar
        if self.tipo == 'teclado':
            self.deposito = 50000.00
        elif self.tipo == 'kit':
            self.deposito = 80000.00
        elif self.tipo == 'pilot':
            # empresas no pagan depósito
            self.deposito = 0.00
        else:
            self.deposito = 50000.00
        super().save(*args, **kwargs)


class Feedback(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]
    nombre = models.CharField(max_length=120, blank=True)
    email = models.EmailField(blank=True)
    rating = models.PositiveSmallIntegerField(choices=RATING_CHOICES)
    comentario = models.TextField(blank=True)
    creado = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.rating} by {self.nombre or self.email or 'anon'}"
