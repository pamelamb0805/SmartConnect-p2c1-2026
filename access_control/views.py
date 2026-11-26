
from django.db.models import Q

from rest_framework import status, viewsets
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import BasePermission, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from people.models import Person
from infrastructure.models import AccessPoint

from .models import Role, PersonRole, Credential, AccessRecord
from .serializers import (
    RoleSerializer,
    PersonRoleSerializer,
    CredentialSerializer,
    AccessRecordSerializer,
    AccessRequestSerializer,
    AccessRecordFilterSerializer,
)
from .pagination import AccessRecordPagination
from .permissions import (
    get_person_for_user,
    get_active_assignments,
    user_can_access_terrain,
)
from .services import evaluate_and_register_access
from datetime import datetime, time, timedelta

from django.utils import timezone

def require_superuser(user):
    if not user.is_superuser:
        raise PermissionDenied(
            "No tienes autorización para realizar esta operación."
        )


class HasLinkedPerson(BasePermission):
    """
    Exige una cuenta autenticada vinculada a una persona.
    """

    message = "Tu cuenta no tiene una persona vinculada."

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and get_person_for_user(request.user) is not None
        )


class IsOwnerOrSuperuser(BasePermission):
    """
    Permite consultar objetos propios o administrarlos
    mediante una cuenta superusuario.
    """

    message = "No tienes autorización para consultar este recurso."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return (
            request.user.is_superuser
            or get_person_for_user(request.user) is not None
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        person = get_person_for_user(request.user)

        if person is None:
            return False

        if isinstance(obj, PersonRole):
            return obj.person_id == person.pk

        if isinstance(obj, Credential):
            return obj.person_id == person.pk

        return False


class CanAccessRecord(BasePermission):
    """
    Permite consultar registros propios o registros
    correspondientes a terrenos autorizados.
    """

    message = "No tienes autorización para consultar este registro."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        return (
            request.user.is_superuser
            or get_person_for_user(request.user) is not None
        )

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        person = get_person_for_user(request.user)

        if person is None:
            return False

        # El titular puede consultar los registros
        # asociados a sus propias credenciales.
        if (
            obj.credential_id
            and obj.credential.person_id == person.pk
        ):
            return True

        # También se permiten registros de puntos de acceso
        # ubicados en terrenos autorizados para la persona.
        return user_can_access_terrain(
            request.user,
            obj.access_point.terrain_id,
        )


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        require_superuser(self.request.user)
        instance.delete()


class PersonRoleViewSet(viewsets.ModelViewSet):
    queryset = PersonRole.objects.select_related(
        "person",
        "role",
        "terrain",
        "dwelling",
    ).all()

    serializer_class = PersonRoleSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_superuser:
            return queryset

        person = get_person_for_user(self.request.user)

        if person is None:
            return queryset.none()

        if self.action == "list":
            return queryset.filter(person=person)

        # Para detalle se conserva el queryset completo:
        # el permiso de objeto responde 403 si no es propio.
        return queryset

    def perform_create(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        require_superuser(self.request.user)
        instance.delete()


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.select_related("person").all()
    serializer_class = CredentialSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrSuperuser]

    def get_queryset(self):
        queryset = super().get_queryset()

        if self.request.user.is_superuser:
            return queryset

        person = get_person_for_user(self.request.user)

        if person is None:
            return queryset.none()

        if self.action == "list":
            return queryset.filter(person=person)

        return queryset

    def perform_create(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_update(self, serializer):
        require_superuser(self.request.user)
        serializer.save()

    def perform_destroy(self, instance):
        require_superuser(self.request.user)
        instance.delete()


class AccessRecordViewSet(viewsets.ModelViewSet):
    queryset = AccessRecord.objects.select_related(
        "access_point",
        "access_point__terrain",
        "credential",
        "credential__person",
    ).all()

    serializer_class = AccessRecordSerializer
    permission_classes = [IsAuthenticated, CanAccessRecord]
    pagination_class = AccessRecordPagination
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user

        if self.action == "list" and not user.is_superuser:
            person = get_person_for_user(user)

            if person is None:
                return queryset.none()

            own_records = Q(
                credential__person_id=person.pk
            )

            terrain_ids = (
                get_active_assignments(user)
                .filter(role__scope=Role.Scope.TERRAIN)
                .values_list("terrain_id", flat=True)
            )

            authorized_records = Q(
                access_point__terrain_id__in=terrain_ids
            )

            queryset = queryset.filter(
                own_records | authorized_records
            ).distinct()

        if self.action == "list":
            filter_serializer = AccessRecordFilterSerializer(
                data=self.request.query_params
            )
            filter_serializer.is_valid(raise_exception=True)
            filters = filter_serializer.validated_data

            if "person" in filters:
                queryset = queryset.filter(
                    credential__person_id=filters["person"]
                )

            if "terrain" in filters:
                queryset = queryset.filter(
                    access_point__terrain_id=filters["terrain"]
                )

            if "access_point" in filters:
                queryset = queryset.filter(
                    access_point_id=filters["access_point"]
                )

            if "result" in filters:
                queryset = queryset.filter(result=filters["result"])

            if "medium" in filters:
                queryset = queryset.filter(medium=filters["medium"])

            if "date_from" in filters:
                fecha_inicio = timezone.make_aware(
                    datetime.combine(filters["date_from"], time.min),
                    timezone.get_current_timezone(),
                )
                queryset = queryset.filter(
                    date_time__gte=fecha_inicio
                )

            if "date_to" in filters:
                fecha_fin = timezone.make_aware(
                    datetime.combine(
                        filters["date_to"] + timedelta(days=1),
                        time.min,
                    ),
                    timezone.get_current_timezone(),
                )
                queryset = queryset.filter(
                    date_time__lt=fecha_fin
                )

        return queryset

    def perform_create(self, serializer):
        require_superuser(self.request.user)

        credential = serializer.validated_data.get("credential")
        uid_received = serializer.validated_data.get(
            "uid_received",
            "",
        )

        if credential and not uid_received:
            uid_received = credential.uid_rfid

        serializer.save(uid_received=uid_received)

class CheckAccessView(APIView):
    """
    Evalúa un intento de acceso físico y registra
    tanto los resultados permitidos como los denegados.

    Una denegación física se responde con HTTP 200
    y autorizado=False; no representa un error 403 de API.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AccessRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        uid_rfid = serializer.validated_data["uid_rfid"]
        access_point_id = serializer.validated_data["access_point_id"]
        medium = serializer.validated_data["medium"]

        access_point = (
            AccessPoint.objects
            .select_related("terrain")
            .filter(pk=access_point_id)
            .first()
        )

        if access_point is None:
            return Response(
                {
                    "error": "El punto de acceso indicado no existe.",
                    "access_point_id": access_point_id,
                },
                status=status.HTTP_404_NOT_FOUND,
            )

        evaluation = evaluate_and_register_access(
            uid_rfid=uid_rfid,
            access_point=access_point,
            medium=medium,
        )

        credential = evaluation["credential"]
        record = evaluation["record"]

        return Response(
            {
                "autorizado": evaluation["allowed"],
                "resultado": evaluation["result"],
                "mensaje": evaluation["description"],
                "registro": record.id_access_record,
                "fecha_hora": record.date_time,
                "uid_recibido": record.uid_received,
                "persona": (
                    str(credential.person)
                    if credential
                    else None
                ),
                "punto_acceso": access_point.name,
                "terreno": access_point.terrain.name,
            },
            status=status.HTTP_200_OK,
        )
