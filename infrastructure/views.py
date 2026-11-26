
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Terrain, Dwelling, AccessPoint
from .serializers import (
    TerrainSerializer,
    DwellingSerializer,
    AccessPointSerializer,
)

from access_control.models import Role
from access_control.permissions import (
    HasScopedAccess,
    get_active_assignments,
)
from django.db import models

class ScopedInfrastructureViewSet(viewsets.ModelViewSet):
    """
    Base para proteger los recursos de infraestructura.

    Los usuarios normales consultan únicamente los recursos
    cubiertos por sus asignaciones PERSONA_ROL vigentes.

    Las operaciones de escritura quedan reservadas a superusuarios
    mientras no exista una matriz de permisos CRUD definida.
    """

    permission_classes = [IsAuthenticated, HasScopedAccess]

    def get_permissions(self):
        """
        Los superusuarios pueden administrar infraestructura
        sin necesitar una asignación PERSONA_ROL.
        """
        if self.request.user and self.request.user.is_superuser:
            return [IsAuthenticated()]

        return super().get_permissions()

    def require_superuser_for_write(self):
        """
        Evita conceder permisos de escritura no definidos
        en el modelo de roles del proyecto.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied(
                "No tienes autorización para realizar esta operación."
            )

    def perform_create(self, serializer):
        self.require_superuser_for_write()
        serializer.save()

    def perform_update(self, serializer):
        self.require_superuser_for_write()
        serializer.save()

    def perform_destroy(self, instance):
        self.require_superuser_for_write()
        instance.delete()


class TerrainViewSet(ScopedInfrastructureViewSet):
    """
    CRUD de terrenos.

    GET     /api/terrenos/
    POST    /api/terrenos/
    GET     /api/terrenos/<id>/
    PUT     /api/terrenos/<id>/
    PATCH   /api/terrenos/<id>/
    DELETE  /api/terrenos/<id>/
    """

    serializer_class = TerrainSerializer

    def get_queryset(self):
        queryset = Terrain.objects.all()

        user = self.request.user

        if user.is_superuser:
            return queryset

        # En detalle se conserva el queryset completo para que
        # HasScopedAccess pueda responder 403 al objeto no autorizado.
        if self.action != "list":
            return queryset

        terrain_ids = (
            get_active_assignments(user)
            .filter(role__scope=Role.Scope.TERRAIN)
            .values_list("terrain_id", flat=True)
        )

        return queryset.filter(
            id_terrain__in=terrain_ids
        ).distinct()


class DwellingViewSet(ScopedInfrastructureViewSet):
    """
    CRUD de viviendas.

    GET     /api/viviendas/
    POST    /api/viviendas/
    GET     /api/viviendas/<id>/
    PUT     /api/viviendas/<id>/
    PATCH   /api/viviendas/<id>/
    DELETE  /api/viviendas/<id>/
    """

    serializer_class = DwellingSerializer

    def get_queryset(self):
        queryset = Dwelling.objects.select_related("terrain").all()

        user = self.request.user

        if user.is_superuser:
            return queryset

        if self.action != "list":
            return queryset

        assignments = get_active_assignments(user)

        # Viviendas autorizadas por asignaciones de ámbito TERRENO.
        terrain_ids = (
            assignments
            .filter(role__scope=Role.Scope.TERRAIN)
            .values_list("terrain_id", flat=True)
        )

        # Viviendas autorizadas por asignaciones de ámbito VIVIENDA.
        dwelling_ids = (
            assignments
            .filter(role__scope=Role.Scope.DWELLING)
            .values_list("dwelling_id", flat=True)
        )

        return queryset.filter(
            models.Q(terrain_id__in=terrain_ids)
            | models.Q(id_dwelling__in=dwelling_ids)
        ).distinct()


class AccessPointViewSet(ScopedInfrastructureViewSet):
    """
    CRUD de puntos de acceso.

    GET     /api/puntos-acceso/
    POST    /api/puntos-acceso/
    GET     /api/puntos-acceso/<id>/
    PUT     /api/puntos-acceso/<id>/
    PATCH   /api/puntos-acceso/<id>/
    DELETE  /api/puntos-acceso/<id>/
    """

    serializer_class = AccessPointSerializer

    def get_queryset(self):
        queryset = AccessPoint.objects.select_related("terrain").all()

        user = self.request.user

        if user.is_superuser:
            return queryset

        if self.action != "list":
            return queryset

        terrain_ids = (
            get_active_assignments(user)
            .filter(role__scope=Role.Scope.TERRAIN)
            .values_list("terrain_id", flat=True)
        )

        return queryset.filter(
            terrain_id__in=terrain_ids
        ).distinct()
