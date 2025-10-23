from __future__ import annotations

import json
from collections import defaultdict
from typing import Dict, List

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Count, Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import FormIngreso, FormRegistro, ReservaForm, RutaForm
from .models import BUS_TOTAL_SEATS, Reserva, Ruta, Usuario


def es_admin(user: Usuario) -> bool:
    return bool(user.es_admin)


def home(request: HttpRequest) -> HttpResponse:
    if not request.user.is_authenticated:
        return redirect("inicio_publico")
    return redirect("inicio_admin" if es_admin(request.user) else "inicio_cliente")


def inicio_publico(request: HttpRequest) -> HttpResponse:
    rutas_destacadas = (
        Ruta.objects.filter(fecha__gte=timezone.localdate())
        .order_by("fecha", "hora_salida")[:3]
    )
    return render(
        request,
        "inicio.html",
        {
            "rutas_destacadas": rutas_destacadas,
            "origenes": [opcion[0] for opcion in Ruta.ORIGENES],
        },
    )


def ingreso_modal(request: HttpRequest) -> HttpResponse:
    registro_form = FormRegistro()
    ingreso_form = FormIngreso(request)

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "registrar":
            registro_form = FormRegistro(request.POST)
            if registro_form.is_valid():
                usuario = registro_form.save()
                login(request, usuario)
                messages.success(request, "Tu cuenta fue creada. Bienvenido.")
                return redirect("inicio_cliente")
            messages.error(request, "Revisa los datos del formulario de registro.")
        else:
            ingreso_form = FormIngreso(request, data=request.POST)
            if ingreso_form.is_valid():
                usuario = ingreso_form.get_user()
                login(request, usuario)
                messages.success(request, "Sesion iniciada correctamente.")
                return redirect("inicio_admin" if es_admin(usuario) else "inicio_cliente")
            messages.error(request, "No pudimos validar las credenciales.")

    return render(
        request,
        "cuenta.html",
        {
            "registro_form": registro_form,
            "ingreso_form": ingreso_form,
        },
    )


@login_required
def inicio_cliente(request: HttpRequest) -> HttpResponse:
    ultimas_reservas = (
        Reserva.objects.filter(usuario=request.user)
        .select_related("ruta")
        .order_by("-fecha_reserva")[:5]
    )
    proximas_rutas = (
        Ruta.objects.filter(fecha__gte=timezone.localdate())
        .order_by("fecha", "hora_salida")[:6]
    )
    return render(
        request,
        "inicio_cliente.html",
        {
            "reservas": ultimas_reservas,
            "proximas_rutas": proximas_rutas,
            "total_asientos": BUS_TOTAL_SEATS,
        },
    )


@login_required
@user_passes_test(es_admin)
def inicio_admin(request: HttpRequest) -> HttpResponse:
    total_usuarios = Usuario.objects.count()
    total_rutas = Ruta.objects.count()
    total_reservas = Reserva.objects.count()
    rutas_top = (
        Ruta.objects.filter(reserva__isnull=False)
        .annotate(total=Count("reserva"))
        .order_by("-total", "fecha")[:5]
    )

    reservas_por_mes: Dict[str, int] = defaultdict(int)
    reservas_qs = Reserva.objects.filter(fecha_reserva__year=timezone.now().year)
    for reserva in reservas_qs:
        reservas_por_mes[reserva.fecha_reserva.strftime("%b")] += 1

    chart_labels = list(reservas_por_mes.keys())
    chart_data = list(reservas_por_mes.values())

    return render(
        request,
        "inicio_admin.html",
        {
            "total_usuarios": total_usuarios,
            "total_rutas": total_rutas,
            "total_reservas": total_reservas,
            "rutas_top": rutas_top,
            "chart_labels_json": json.dumps(chart_labels),
            "chart_data_json": json.dumps(chart_data),
        },
    )


def salir(request: HttpRequest) -> HttpResponse:
    logout(request)
    messages.info(request, "Cerraste sesion correctamente.")
    return redirect("inicio_publico")


@login_required
@user_passes_test(es_admin)
def listar_rutas(request: HttpRequest) -> HttpResponse:
    rutas = Ruta.objects.all().order_by("fecha", "hora_salida")
    consulta = request.GET.get("q")

    if consulta:
        rutas = rutas.filter(
            Q(origen__icontains=consulta)
            | Q(destino__icontains=consulta)
            | Q(fecha__icontains=consulta)
        )

    return render(
        request,
        "rutas/listar_rutas.html",
        {"rutas": rutas, "consulta": consulta or ""},
    )


@login_required
@user_passes_test(es_admin)
def crear_ruta(request: HttpRequest) -> HttpResponse:
    form = RutaForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La ruta se registro correctamente.")
        return redirect("listar_rutas")

    return render(request, "rutas/crear_ruta.html", {"form": form})


@login_required
@user_passes_test(es_admin)
def editar_ruta(request: HttpRequest, pk: int) -> HttpResponse:
    ruta = get_object_or_404(Ruta, pk=pk)
    form = RutaForm(request.POST or None, instance=ruta)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "La ruta fue actualizada.")
        return redirect("listar_rutas")

    return render(
        request,
        "rutas/crear_ruta.html",
        {"form": form, "modo_edicion": True, "ruta": ruta},
    )


@login_required
@user_passes_test(es_admin)
def eliminar_ruta(request: HttpRequest, pk: int) -> HttpResponse:
    ruta = get_object_or_404(Ruta, pk=pk)

    if request.method == "POST":
        ruta.delete()
        messages.success(request, "La ruta fue eliminada.")
        return redirect("listar_rutas")

    return render(request, "rutas/confirmar_eliminar.html", {"ruta": ruta})


def _filtrar_rutas(request: HttpRequest) -> Dict[str, object]:
    rutas = Ruta.objects.filter(fecha__gte=timezone.localdate()).order_by("fecha", "hora_salida")
    origen = request.GET.get("origen") or ""
    destino = request.GET.get("destino") or ""
    fecha = request.GET.get("fecha") or ""

    if origen:
        rutas = rutas.filter(origen=origen)
    if destino:
        rutas = rutas.filter(destino=destino)
    if fecha:
        rutas = rutas.filter(fecha=fecha)

    return {
        "rutas": rutas,
        "origen": origen,
        "destino": destino,
        "fecha": fecha,
        "origenes": [opcion[0] for opcion in Ruta.ORIGENES],
    }


def rutas_disponibles(request: HttpRequest) -> HttpResponse:
    contexto = _filtrar_rutas(request)
    return render(request, "rutas/rutas_disponibles.html", contexto)


@login_required
def listar_rutas_cliente(request: HttpRequest) -> HttpResponse:
    contexto = _filtrar_rutas(request)
    return render(request, "rutas/listar_ruta_cliente.html", contexto)


@login_required
def reservar_ruta(request: HttpRequest, pk: int) -> HttpResponse:
    ruta = get_object_or_404(Ruta, pk=pk)
    ocupados = list(Reserva.objects.filter(ruta=ruta).values_list("asiento", flat=True))
    form = ReservaForm(request.POST or None, ruta=ruta, ocupados=ocupados)

    if request.method == "POST" and form.is_valid():
        asientos: List[int] = form.cleaned_data["asientos"]
        nuevas_reservas = [
            Reserva(usuario=request.user, ruta=ruta, asiento=asiento) for asiento in asientos
        ]
        Reserva.objects.bulk_create(nuevas_reservas)
        seats_txt = ", ".join(str(asiento) for asiento in asientos)
        messages.success(request, f"Reservaste los asientos {seats_txt} para la ruta seleccionada.")
        return redirect("mis_reservas")

    return render(
        request,
        "rutas/confirmar_reserva.html",
        {
            "ruta": ruta,
            "form": form,
            "ocupados": ocupados,
            "total_asientos": BUS_TOTAL_SEATS,
        },
    )


@login_required
def mis_reservas(request: HttpRequest) -> HttpResponse:
    reservas = (
        Reserva.objects.filter(usuario=request.user)
        .select_related("ruta")
        .order_by("-fecha_reserva")
    )
    return render(request, "rutas/mis_reservas.html", {"reservas": reservas})


@login_required
def seleccionar_asiento(request: HttpRequest, ruta_id: int) -> HttpResponse:
    return redirect("reservar_ruta", pk=ruta_id)
