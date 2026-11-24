from rest_framework.routers import DefaultRouter

from .views import (
    TerrainViewSet,
    DwellingViewSet,
    AccessPointViewSet,
)

router = DefaultRouter()

router.register(r"terrenos", TerrainViewSet, basename="terreno")
router.register(r"viviendas", DwellingViewSet, basename="vivienda")
router.register(r"puntos-acceso", AccessPointViewSet, basename="punto-acceso")

urlpatterns = router.urls