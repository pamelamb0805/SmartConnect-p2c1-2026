
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied

from .models import Person
from .serializers import PersonSerializer


class PersonViewSet(viewsets.ModelViewSet):
    """
    CRUD de personas protegido mediante JWT.

    GET     /api/personas/
    POST    /api/personas/
    GET     /api/personas/<id>/
    PUT     /api/personas/<id>/
    PATCH   /api/personas/<id>/
    DELETE  /api/personas/<id>/

    Los usuarios normales solamente pueden consultar y modificar
    su propio registro de persona.

    La creación y eliminación quedan reservadas a superusuarios.
    """

    serializer_class = PersonSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """
        Evita que un usuario consulte personas ajenas.
        Los superusuarios pueden consultar todos los registros.
        """
        user = self.request.user

        if user.is_superuser:
            return Person.objects.all()

        return Person.objects.filter(user=user)

    def perform_create(self, serializer):
        """
        Solamente un superusuario puede crear personas.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied(
                "No tienes autorización para registrar personas."
            )

        serializer.save()

    def perform_update(self, serializer):
        """
        Evita que un usuario cambie la cuenta vinculada
        a su propia persona.
        """
        if self.request.user.is_superuser:
            serializer.save()
            return

        serializer.save(user=self.request.user)

    def perform_destroy(self, instance):
        """
        Solamente un superusuario puede eliminar personas.
        """
        if not self.request.user.is_superuser:
            raise PermissionDenied(
                "No tienes autorización para eliminar personas."
            )

        instance.delete()
