
from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)


def api_home(request):
    return JsonResponse({
        "proyecto": "SmartConnect API",
        "mensaje": "API funcionando correctamente.",
        "endpoints": {
            "personas": "/api/personas/",
            "terrenos": "/api/terrenos/",
            "viviendas": "/api/viviendas/",
            "puntos_acceso": "/api/puntos-acceso/",
            "roles": "/api/access-control/roles/",
            "asignaciones_roles": "/api/access-control/person-roles/",
            "credenciales": "/api/access-control/credentials/",
            "registros_acceso": "/api/access-control/access-records/",
            "token": "/api/token/",
            "renovar_token": "/api/token/refresh/",
            "administracion": "/admin/",
        },
    })


urlpatterns = [
    # Inicio de la API
    path("", api_home, name="api-home"),

    # Administración Django
    path("admin/", admin.site.urls),

    # API de personas
    path("api/", include("people.urls")),

    # API de infraestructura
    path("api/", include("infrastructure.urls")),

    # API de control de acceso
    path(
        "api/access-control/",
        include("access_control.urls"),
    ),

    # Autenticación JWT
    path(
        "api/token/",
        TokenObtainPairView.as_view(),
        name="token_obtain_pair",
    ),
    path(
        "api/token/refresh/",
        TokenRefreshView.as_view(),
        name="token_refresh",
    ),
]
