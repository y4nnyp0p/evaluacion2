from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario, Ruta, Reserva

class UsuarioAdmin(UserAdmin):
    model = Usuario
    list_display = ('username', 'email', 'es_admin', 'is_staff')
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('es_admin',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('es_admin',)}),
    )

admin.site.register(Usuario, UsuarioAdmin)

@admin.register(Ruta)
class RutaAdmin(admin.ModelAdmin):
    list_display = ('origen', 'destino', 'fecha', 'hora_salida', 'precio')
    search_fields = ('origen', 'destino')
    list_filter = ('origen', 'destino', 'fecha')


# ==== RESERVAS ====
@admin.register(Reserva)
class ReservaAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'ruta', 'asiento', 'fecha_reserva')
    list_filter = ('ruta', 'fecha_reserva')

