
from rest_framework import viewsets
from rest_framework.permissions import AllowAny
from rest_framework.exceptions import ValidationError

from .models import Role, PersonRole, Credential, AccessRecord
from .serializers import (
    RoleSerializer,
    PersonRoleSerializer,
    CredentialSerializer,
    AccessRecordSerializer,
)


class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [AllowAny]


class PersonRoleViewSet(viewsets.ModelViewSet):
    queryset = PersonRole.objects.select_related(
        "person",
        "role",
        "terrain",
        "dwelling",
    ).all()
    serializer_class = PersonRoleSerializer
    permission_classes = [AllowAny]


class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.select_related("person").all()
    serializer_class = CredentialSerializer
    permission_classes = [AllowAny]


class AccessRecordViewSet(viewsets.ModelViewSet):
    queryset = AccessRecord.objects.select_related(
        "access_point",
        "credential",
        "credential__person",
    ).all()
    serializer_class = AccessRecordSerializer
    permission_classes = [AllowAny]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()

        person_id = self.request.query_params.get("person")
        terrain_id = self.request.query_params.get("terrain")
        access_point_id = self.request.query_params.get("access_point")
        result = self.request.query_params.get("result")
        medium = self.request.query_params.get("medium")
        date_from = self.request.query_params.get("date_from")
        date_to = self.request.query_params.get("date_to")

        if person_id:
            queryset = queryset.filter(
                credential__person_id=person_id
            )

        if terrain_id:
            queryset = queryset.filter(
                access_point__terrain_id=terrain_id
            )

        if access_point_id:
            queryset = queryset.filter(
                access_point_id=access_point_id
            )

        if result:
            queryset = queryset.filter(result=result)

        if medium:
            queryset = queryset.filter(medium=medium)

        if date_from:
            queryset = queryset.filter(date_time__date__gte=date_from)

        if date_to:
            queryset = queryset.filter(date_time__date__lte=date_to)

        return queryset

    def perform_create(self, serializer):
        credential = serializer.validated_data.get("credential")
        uid_received = serializer.validated_data.get("uid_received", "")

        if credential and not uid_received:
            uid_received = credential.uid_rfid

        serializer.save(uid_received=uid_received)
