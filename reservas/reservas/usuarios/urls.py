from django.urls import path

from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("index/", views.inicio_publico, name="inicio_publico"),
    path("cliente/", views.inicio_cliente, name="inicio_cliente"),
    path("index_admin/", views.inicio_admin, name="inicio_admin"),
    path("ingreso/", views.ingreso_modal, name="ingreso_modal"),
    path("salir/", views.salir, name="salir"),
    path("rutas/", views.listar_rutas, name="listar_rutas"),
    path("rutas/crear/", views.crear_ruta, name="crear_ruta"),
    path("rutas/editar/<int:pk>/", views.editar_ruta, name="editar_ruta"),
    path("rutas/eliminar/<int:pk>/", views.eliminar_ruta, name="eliminar_ruta"),
    path("rutas/disponibles/", views.rutas_disponibles, name="rutas_disponibles"),
    path("rutas/clientes/", views.listar_rutas_cliente, name="listar_rutas_cliente"),
    path("rutas/reservar/<int:pk>/", views.reservar_ruta, name="reservar_ruta"),
    path("rutas/mis-reservas/", views.mis_reservas, name="mis_reservas"),
    path("rutas/<int:ruta_id>/asientos/", views.seleccionar_asiento, name="seleccionar_asiento"),
]
