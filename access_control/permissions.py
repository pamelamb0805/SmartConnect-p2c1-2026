
from django.db.models import Q
from django.utils import timezone

from rest_framework.permissions import BasePermission

from people.models import Person
from .models import PersonRole, Role


def get_person_for_user(user):
    """
    Obtiene la persona vinculada a la cuenta autenticada.
    Retorna None si la cuenta no tiene una persona asociada.
    """
    if not user or not user.is_authenticated:
        return None

    return Person.objects.filter(user_id=user.pk).first()


def get_active_assignments(user):
    """
    Obtiene las asignaciones PERSONA_ROL vigentes del usuario.

    Se consideran:
    - Persona vinculada a la cuenta.
    - Asignación activa.
    - Rol activo.
    - Fecha de inicio alcanzada.
    - Fecha de término no vencida.
    """
    person = get_person_for_user(user)

    if person is None:
        return PersonRole.objects.none()

    today = timezone.localdate()

    return (
        PersonRole.objects
        .select_related(
            "person",
            "role",
            "terrain",
            "dwelling",
            "dwelling__terrain",
        )
        .filter(
            person=person,
            status=PersonRole.Status.ACTIVE,
            role__status=Role.Status.ACTIVE,
            start_date__lte=today,
        )
        .filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=today)
        )
    )


def user_can_access_terrain(user, terrain_id):
    """
    Comprueba si el usuario tiene una asignación vigente
    de ámbito TERRENO para el terreno indicado.
    """
    if not terrain_id:
        return False

    return get_active_assignments(user).filter(
        role__scope=Role.Scope.TERRAIN,
        terrain_id=terrain_id,
    ).exists()


def user_can_access_dwelling(user, dwelling_id):
    """
    Comprueba si el usuario puede acceder a una vivienda.

    Se autoriza cuando:
    - Tiene un rol TERRENO asociado al terreno de la vivienda.
    - Tiene un rol VIVIENDA asociado exactamente a esa vivienda.

    Una asignación VIVIENDA no concede acceso a otras viviendas.
    """
    if not dwelling_id:
        return False

    assignments = get_active_assignments(user)

    return assignments.filter(
        Q(
            role__scope=Role.Scope.TERRAIN,
            terrain__dwellings__id_dwelling=dwelling_id,
        )
        |
        Q(
            role__scope=Role.Scope.DWELLING,
            dwelling_id=dwelling_id,
        )
    ).exists()


class HasScopedAccess(BasePermission):
    """
    Permiso de acceso según las asignaciones PERSONA_ROL.

    Comprueba el ámbito del objeto solicitado:
    - Terrain: asignación TERRENO.
    - Dwelling: asignación TERRENO o VIVIENDA.
    - AccessPoint: asignación TERRENO del terreno asociado.

    Esta clase realiza comprobaciones a nivel de objeto.
    Los listados deben filtrarse también en get_queryset()
    para evitar mostrar objetos no autorizados.
    """

    message = (
        "No tienes una asignación vigente que autorice "
        "el acceso a este recurso."
    )

    def has_permission(self, request, view):
        """
        Exige autenticación y una persona vinculada a la cuenta.
        """
        user = request.user

        if not user or not user.is_authenticated:
            return False

        return get_person_for_user(user) is not None

    def has_object_permission(self, request, view, obj):
        """
        Comprueba la autorización sobre el objeto específico.
        """

        # Objetos asociados directamente a un terreno.
        if hasattr(obj, "terrain_id"):
            terrain_id = obj.terrain_id

            # Si el objeto representa una vivienda,
            # se comprueba su asignación específica o la del terreno.
            if hasattr(obj, "id_dwelling"):
                return user_can_access_dwelling(
                    request.user,
                    obj.id_dwelling,
                )

            return user_can_access_terrain(
                request.user,
                terrain_id,
            )

        # Objeto de tipo terreno.
        if hasattr(obj, "id_terrain"):
            return user_can_access_terrain(
                request.user,
                obj.id_terrain,
            )

        return False
