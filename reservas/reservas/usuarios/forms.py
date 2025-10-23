from datetime import datetime

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import BUS_TOTAL_SEATS, Ruta, Usuario


class FormRegistro(UserCreationForm):
    email = forms.EmailField(
        label="Correo",
        required=True,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "correo@ejemplo.com"}),
    )

    class Meta:
        model = Usuario
        fields = ("username", "email", "password1", "password2")
        labels = {"username": "Usuario"}
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Nombre de usuario"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contrasena"}),
            "password2": forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "Repite la contrasena"}
            ),
        }

    def clean_username(self):
        usuario = self.cleaned_data["username"]
        if Usuario.objects.filter(username__iexact=usuario).exists():
            raise ValidationError("Ya existe un usuario con ese nombre.")
        return usuario

    def clean_email(self):
        correo = self.cleaned_data["email"]
        if Usuario.objects.filter(email__iexact=correo).exists():
            raise ValidationError("Ya existe una cuenta con ese correo.")
        return correo

    def save(self, commit: bool = True) -> Usuario:
        user = super().save(commit=False)
        # Los registros publicos siempre quedan como clientes
        user.es_admin = False
        user.is_staff = False
        user.is_superuser = False
        if commit:
            user.save()
        return user


class FormIngreso(AuthenticationForm):
    username = forms.CharField(
        label="Usuario o correo",
        widget=forms.TextInput(attrs={"autofocus": True, "class": "form-control", "placeholder": "usuario o correo"}),
    )
    password = forms.CharField(
        label="Contrasena",
        strip=False,
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Contrasena"}),
    )

    def clean(self):
        username = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username and password:
            self.user_cache = authenticate(self.request, username=username, password=password)

            if self.user_cache is None:
                try:
                    usuario = Usuario.objects.get(email__iexact=username)
                except Usuario.DoesNotExist as exc:
                    raise self.get_invalid_login_error() from exc

                self.user_cache = authenticate(self.request, username=usuario.username, password=password)

            if self.user_cache is None:
                raise self.get_invalid_login_error()

            self.confirm_login_allowed(self.user_cache)

        return self.cleaned_data


class RutaForm(forms.ModelForm):
    class Meta:
        model = Ruta
        fields = ["origen", "destino", "fecha", "hora_salida", "precio"]
        widgets = {
            "origen": forms.Select(attrs={"class": "form-select"}),
            "destino": forms.Select(attrs={"class": "form-select"}),
            "fecha": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hora_salida": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "precio": forms.NumberInput(attrs={"class": "form-control", "min": "0", "step": "0.01"}),
        }

    def clean(self):
        cleaned_data = super().clean()
        origen = cleaned_data.get("origen")
        destino = cleaned_data.get("destino")
        fecha = cleaned_data.get("fecha")
        hora = cleaned_data.get("hora_salida")
        precio = cleaned_data.get("precio")

        if not origen or not destino:
            raise ValidationError("Selecciona un origen y un destino.")

        if origen == destino:
            raise ValidationError("El origen y el destino deben ser diferentes.")

        if fecha and hora:
            salida = datetime.combine(fecha, hora)
            if timezone.is_naive(salida):
                salida = timezone.make_aware(salida, timezone.get_current_timezone())
            if salida < timezone.now():
                raise ValidationError("La fecha y hora de salida deben ser futuras.")
        elif fecha and fecha < timezone.localdate():
            raise ValidationError("La fecha de la ruta no puede estar en el pasado.")

        if precio is not None and precio <= 0:
            raise ValidationError("El precio debe ser mayor que cero.")

        return cleaned_data


class ReservaForm(forms.Form):
    asientos = forms.CharField(widget=forms.HiddenInput())

    def __init__(self, *args, ruta=None, ocupados=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.ruta = ruta
        self._ocupados = {int(v) for v in ocupados} if ocupados else set()

    def clean_asientos(self):
        raw_value = self.cleaned_data.get("asientos", "")
        tokens = [token.strip() for token in raw_value.split(",") if token.strip()]

        if not tokens:
            raise ValidationError("Selecciona al menos un asiento disponible.")

        try:
            seats = [int(token) for token in tokens]
        except ValueError as exc:
            raise ValidationError("Selecciona asientos validos.") from exc

        if len(seats) != len(set(seats)):
            raise ValidationError("No repitas asientos.")

        invalid = [seat for seat in seats if seat < 1 or seat > BUS_TOTAL_SEATS]
        if invalid:
            raise ValidationError(f"Los asientos deben estar entre 1 y {BUS_TOTAL_SEATS}.")

        ocupados = [seat for seat in seats if seat in self._ocupados]
        if ocupados:
            seats_txt = ", ".join(str(seat) for seat in ocupados)
            raise ValidationError(f"Los asientos {seats_txt} ya fueron reservados.")

        return seats
