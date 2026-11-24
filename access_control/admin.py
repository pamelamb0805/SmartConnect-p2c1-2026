
from django.contrib import admin
from .models import Role, PersonRole, Credential, AccessRecord


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id_role", "name", "scope", "status")
    list_filter = ("scope", "status")
    search_fields = ("name", "description")


@admin.register(PersonRole)
class PersonRoleAdmin(admin.ModelAdmin):
    list_display = (
        "id_person_role",
        "person",
        "role",
        "terrain",
        "dwelling",
        "start_date",
        "end_date",
        "status",
    )
    list_filter = ("status", "role__scope", "start_date")
    search_fields = (
        "person__rut",
        "person__first_name",
        "person__last_name",
        "role__name",
    )
    autocomplete_fields = ("person", "role", "terrain", "dwelling")


@admin.register(Credential)
class CredentialAdmin(admin.ModelAdmin):
    list_display = ("id_credential", "uid_rfid", "person", "status")
    list_filter = ("status",)
    search_fields = (
        "uid_rfid",
        "person__rut",
        "person__first_name",
        "person__last_name",
    )
    autocomplete_fields = ("person",)


@admin.register(AccessRecord)
class AccessRecordAdmin(admin.ModelAdmin):
    list_display = (
        "id_access_record",
        "date_time",
        "medium",
        "result",
        "access_point",
        "credential",
        "uid_received",
    )
    list_filter = ("result", "medium", "date_time")
    search_fields = (
        "uid_received",
        "credential__uid_rfid",
        "access_point__name",
        "description",
    )
    readonly_fields = ("date_time",)
    date_hierarchy = "date_time"
