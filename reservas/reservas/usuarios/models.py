from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models


BUS_TOTAL_SEATS = 40


class Usuario(AbstractUser):
    email = models.EmailField("correo", unique=True)
    es_admin = models.BooleanField("es admin", default=False)

    def __str__(self) -> str:
        return self.username


COORDENADAS = {
    "Santiago": {"lat": -33.4489, "lng": -70.6693},
    "Valparaiso": {"lat": -33.0458, "lng": -71.6197},
    "Concepcion": {"lat": -36.8201, "lng": -73.0444},
}


class Ruta(models.Model):
    ORIGENES = [
        ("Santiago", "Santiago"),
        ("Valparaiso", "Valparaiso"),
        ("Concepcion", "Concepcion"),
    ]
    DESTINOS = ORIGENES

    origen = models.CharField(max_length=50, choices=ORIGENES)
    destino = models.CharField(max_length=50, choices=DESTINOS)
    origen_lat = models.FloatField(null=True, blank=True)
    origen_lng = models.FloatField(null=True, blank=True)
    destino_lat = models.FloatField(null=True, blank=True)
    destino_lng = models.FloatField(null=True, blank=True)
    fecha = models.DateField()
    hora_salida = models.TimeField()
    precio = models.DecimalField(max_digits=7, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.origen} -> {self.destino} | {self.fecha} {self.hora_salida}"


class Reserva(models.Model):
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    ruta = models.ForeignKey(Ruta, on_delete=models.CASCADE)
    asiento = models.PositiveIntegerField()
    fecha_reserva = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.usuario.username} - {self.ruta} (Asiento {self.asiento})"
