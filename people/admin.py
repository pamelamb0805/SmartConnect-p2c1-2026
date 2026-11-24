from django.contrib import admin

from .models import Person


@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = (
        "id_person",
        "rut",
        "first_name",
        "last_name",
        "email",
        "phone",
    )

    search_fields = (
        "rut",
        "first_name",
        "last_name",
        "email",
    )

    ordering = (
        "last_name",
        "first_name",
    )