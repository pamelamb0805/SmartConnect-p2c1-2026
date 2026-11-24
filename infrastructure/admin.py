from django.contrib import admin

from .models import Terrain, Dwelling, AccessPoint


@admin.register(Terrain)
class TerrainAdmin(admin.ModelAdmin):
    list_display = (
        "id_terrain",
        "name",
        "address",
        "status",
    )

    list_filter = (
        "status",
    )

    search_fields = (
        "name",
        "address",
    )


@admin.register(Dwelling)
class DwellingAdmin(admin.ModelAdmin):
    list_display = (
        "id_dwelling",
        "identifier_number",
        "dwelling_type",
        "address",
        "terrain",
        "status",
    )

    list_filter = (
        "dwelling_type",
        "status",
        "terrain",
    )

    search_fields = (
        "identifier_number",
        "address",
        "terrain__name",
    )

    autocomplete_fields = (
        "terrain",
    )


@admin.register(AccessPoint)
class AccessPointAdmin(admin.ModelAdmin):
    list_display = (
        "id_access_point",
        "name",
        "point_type",
        "terrain",
        "status",
    )

    list_filter = (
        "point_type",
        "status",
        "terrain",
    )

    search_fields = (
        "name",
        "terrain__name",
    )

    autocomplete_fields = (
        "terrain",
    )