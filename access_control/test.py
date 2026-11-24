
from datetime import timedelta

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from people.models import Person
from infrastructure.models import Terrain, AccessPoint
from .models import (
    Role,
    PersonRole,
    Credential,
    AccessRecord,
)


class CheckAccessTests(TestCase):

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("check-access")
        self.today = timezone.localdate()

        # Persona
        self.person = Person.objects.create(
            rut="11111111-1",
            first_name="Ana",
            last_name="Prueba",
            email="ana@example.com",
            phone="912345678",
        )

        # Terreno
        self.terrain = Terrain.objects.create(
            name="Terreno de prueba",
            address="Dirección de prueba",
            status="ACTIVO",
        )

        # Punto de acceso
        self.access_point = AccessPoint.objects.create(
            name="Portón principal",
            point_type="PORTON",
            status="ACTIVO",
            terrain=self.terrain,
        )

        # Rol asociado al terreno
        self.role = Role.objects.create(
            name="Propietario de prueba",
            description="Rol utilizado en pruebas automatizadas",
            scope=Role.Scope.TERRAIN,
            status=Role.Status.ACTIVE,
        )

        # Asignación vigente
        self.assignment = PersonRole.objects.create(
            person=self.person,
            role=self.role,
            start_date=self.today - timedelta(days=10),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            terrain=self.terrain,
            dwelling=None,
        )

        # Credencial RFID
        self.credential = Credential.objects.create(
            uid_rfid="RFID-TEST-001",
            status=Credential.Status.ACTIVE,
            person=self.person,
        )

    def send_request(self, uid="RFID-TEST-001", point_id=None):
        return self.client.post(
            self.url,
            {
                "uid_rfid": uid,
                "access_point_id": (
                    point_id or self.access_point.pk
                ),
                "medium": "RFID",
            },
            format="json",
        )

    def test_credencial_vigente_y_rol_activo_permiten_acceso(self):
        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["autorizado"])
        self.assertEqual(
            response.data["resultado"],
            AccessRecord.Result.ALLOWED,
        )
        self.assertEqual(AccessRecord.objects.count(), 1)

    def test_uid_desconocido_deniega_y_registra_intento(self):
        response = self.send_request(uid="UID-DESCONOCIDO")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])
        self.assertEqual(
            response.data["resultado"],
            AccessRecord.Result.DENIED,
        )

        record = AccessRecord.objects.get()

        self.assertEqual(record.uid_received, "UID-DESCONOCIDO")
        self.assertIsNone(record.credential)

    def test_credencial_bloqueada_deniega_acceso(self):
        self.credential.status = Credential.Status.BLOCKED
        self.credential.save()

        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])
        self.assertEqual(
            response.data["resultado"],
            AccessRecord.Result.DENIED,
        )

    def test_asignacion_vencida_deniega_acceso(self):
        self.assignment.end_date = self.today - timedelta(days=1)
        self.assignment.save()

        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_rol_inactivo_deniega_acceso(self):
        self.role.status = Role.Status.INACTIVE
        self.role.save()

        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_punto_acceso_inactivo_deniega_acceso(self):
        self.access_point.status = "INACTIVO"
        self.access_point.save()

        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_terreno_inactivo_deniega_acceso(self):
        self.terrain.status = "INACTIVO"
        self.terrain.save()

        response = self.send_request()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_punto_acceso_inexistente_devuelve_404(self):
        response = self.send_request(point_id=999999)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(AccessRecord.objects.count(), 0)
