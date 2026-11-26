from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from .models import Terrain, Dwelling, AccessPoint
from .serializers import (
    TerrainSerializer,
    DwellingSerializer,
    AccessPointSerializer,
)


class TerrainViewSet(viewsets.ModelViewSet):
    """
    CRUD de terrenos.

    GET     /api/terrenos/
    POST    /api/terrenos/
    GET     /api/terrenos/<id>/
    PUT     /api/terrenos/<id>/
    PATCH   /api/terrenos/<id>/
    DELETE  /api/terrenos/<id>/
    """

    queryset = Terrain.objects.all()
    serializer_class = TerrainSerializer
    permission_classes = [AllowAny]


class DwellingViewSet(viewsets.ModelViewSet):
    """
    CRUD de viviendas.

    GET     /api/viviendas/
    POST    /api/viviendas/
    GET     /api/viviendas/<id>/
    PUT     /api/viviendas/<id>/
    PATCH   /api/viviendas/<id>/
    DELETE  /api/viviendas/<id>/
    """

    queryset = Dwelling.objects.select_related("terrain").all()
    serializer_class = DwellingSerializer
    permission_classes = [IsAuthenticated]

class AccessPointViewSet(viewsets.ModelViewSet):
    """
    CRUD de puntos de acceso.

    GET     /api/puntos-acceso/
    POST    /api/puntos-acceso/
    GET     /api/puntos-acceso/<id>/
    PUT     /api/puntos-acceso/<id>/
    PATCH   /api/puntos-acceso/<id>/
    DELETE  /api/puntos-acceso/<id>/
    """

    queryset = AccessPoint.objects.select_related("terrain").all()
    serializer_class = AccessPointSerializer
    permission_classes = [AllowAny]