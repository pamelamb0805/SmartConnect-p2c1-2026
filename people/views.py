from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from .models import Person
from .serializers import PersonSerializer


class PersonViewSet(viewsets.ModelViewSet):
    """
    CRUD de personas.

    GET     /api/personas/
    POST    /api/personas/
    GET     /api/personas/<id>/
    PUT     /api/personas/<id>/
    PATCH   /api/personas/<id>/
    DELETE  /api/personas/<id>/
    """

    queryset = Person.objects.all()
    serializer_class = PersonSerializer
    permission_classes = [AllowAny]