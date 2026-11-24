
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError

from .models import Role, PersonRole, Credential, AccessRecord
from .serializers import (
    RoleSerializer,
    PersonRoleSerializer,
    CredentialSerializer,
    AccessRecordSerializer,
)

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from infrastructure.models import AccessPoint
from .services import evaluate_and_register_access
from .serializers import AccessRequestSerializer
from .pagination import AccessRecordPagination
from rest_framework.permissions import AllowAny

class RoleViewSet(viewsets.ModelViewSet):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsAuthenticated]


class PersonRoleViewSet(viewsets.ModelViewSet):
    queryset = PersonRole.objects.select_related(
        "person",
        "role",
        "terrain",
        "dwelling",
    ).all()
    serializer_class = PersonRoleSerializer
    permission_classes = [IsAuthenticated]

class CredentialViewSet(viewsets.ModelViewSet):
    queryset = Credential.objects.select_related("person").all()
    serializer_class = CredentialSerializer
    permission_classes = [IsAuthenticated]



class AccessRecordViewSet(viewsets.ModelViewSet):
    queryset = AccessRecord.objects.select_related(
        "access_point",
        "access_point__terrain",
        "credential",
        "credential__person",
    ).all()

    serializer_class = AccessRecordSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = AccessRecordPagination

    # El historial no puede modificarse ni eliminarse mediante la API.
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        from .serializers import AccessRecordFilterSerializer

        queryset = super().get_queryset()

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
            queryset = queryset.filter(
                result=filters["result"]
            )

        if "medium" in filters:
            queryset = queryset.filter(
                medium=filters["medium"]
            )

        if "date_from" in filters:
            queryset = queryset.filter(
                date_time__date__gte=filters["date_from"]
            )

        if "date_to" in filters:
            queryset = queryset.filter(
                date_time__date__lte=filters["date_to"]
            )

        return queryset

    def perform_create(self, serializer):
        credential = serializer.validated_data.get("credential")
        uid_received = serializer.validated_data.get(
            "uid_received",
            "",
        )

        if credential and not uid_received:
            uid_received = credential.uid_rfid

        serializer.save(uid_received=uid_received)
        
class CheckAccessView(APIView):
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