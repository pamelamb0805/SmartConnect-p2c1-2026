
from datetime import timedelta

from django.contrib.auth import get_user_model
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


class AccessControlTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        User = get_user_model()

        self.user = User.objects.create_superuser(
            username="admin_access_test",
            email="admin.access@test.cl",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=self.user)

        self.person = Person.objects.create(
            rut="11111111-1",
            first_name="Persona",
            last_name="Prueba",
            email="persona@smartconnect.cl",
            phone="912345678",
        )

        self.terrain = Terrain.objects.create(
            name="Terreno de prueba",
            address="Dirección de prueba",
            status="ACTIVO",
        )

        self.access_point = AccessPoint.objects.create(
            name="Acceso principal",
            point_type="PORTON",
            status="ACTIVO",
            terrain=self.terrain,
        )

        self.role = Role.objects.create(
            name="Administrador de prueba",
            description="Rol para pruebas automatizadas",
            scope=Role.Scope.TERRAIN,
            status=Role.Status.ACTIVE,
        )

        self.credential = Credential.objects.create(
            uid_rfid="RFID-TEST-001",
            status=Credential.Status.ACTIVE,
            person=self.person,
        )

        self.assignment = PersonRole.objects.create(
            person=self.person,
            role=self.role,
            start_date=timezone.localdate() - timedelta(days=5),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            terrain=self.terrain,
        )

        self.check_url = reverse("check-access")
        self.history_url = reverse("access-record-list")

    def check_access(self, uid="RFID-TEST-001", point_id=None):
        return self.client.post(
            self.check_url,
            {
                "uid_rfid": uid,
                "access_point_id": (
                    point_id or self.access_point.pk
                ),
                "medium": "RFID",
            },
            format="json",
        )

    def test_credencial_activa_y_rol_vigente_permiten_acceso(self):
        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["autorizado"])
        self.assertEqual(
            response.data["resultado"],
            AccessRecord.Result.ALLOWED,
        )
        self.assertEqual(AccessRecord.objects.count(), 1)

    def test_uid_desconocido_deniega_y_registra_intento(self):
        response = self.check_access(uid="UID-DESCONOCIDO")

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])
        self.assertEqual(
            response.data["resultado"],
            AccessRecord.Result.DENIED,
        )

        record = AccessRecord.objects.get()

        self.assertEqual(
            record.uid_received,
            "UID-DESCONOCIDO",
        )
        self.assertIsNone(record.credential)

    def test_credencial_bloqueada_deniega_acceso(self):
        self.credential.status = Credential.Status.BLOCKED
        self.credential.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_credencial_inactiva_deniega_acceso(self):
        self.credential.status = Credential.Status.INACTIVE
        self.credential.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_asignacion_vencida_deniega_acceso(self):
        self.assignment.end_date = (
            timezone.localdate() - timedelta(days=1)
        )
        self.assignment.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_rol_inactivo_deniega_acceso(self):
        self.role.status = Role.Status.INACTIVE
        self.role.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_punto_acceso_inactivo_deniega_acceso(self):
        self.access_point.status = "INACTIVO"
        self.access_point.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_terreno_inactivo_deniega_acceso(self):
        self.terrain.status = "INACTIVO"
        self.terrain.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

    def test_punto_acceso_inexistente_responde_404(self):
        response = self.check_access(point_id=999999)

        self.assertEqual(response.status_code, 404)
        self.assertEqual(AccessRecord.objects.count(), 0)

    def test_asignacion_de_otro_terreno_no_autoriza(self):
        otro_terreno = Terrain.objects.create(
            name="Otro terreno",
            address="Otra dirección",
            status="ACTIVO",
        )

        self.assignment.terrain = otro_terreno
        self.assignment.save()

        response = self.check_access()

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])


class AccessRecordFilterTests(TestCase):

    def setUp(self):
        self.client = APIClient()

        User = get_user_model()

        self.user = User.objects.create_superuser(
            username="admin_historial_test",
            email="admin.historial@test.cl",
            password="TestPassword123!",
        )

        self.client.force_authenticate(user=self.user)

        self.person = Person.objects.create(
            rut="22222222-2",
            first_name="Historial",
            last_name="Prueba",
        )

        self.other_person = Person.objects.create(
            rut="33333333-3",
            first_name="Otra",
            last_name="Persona",
        )

        self.terrain = Terrain.objects.create(
            name="Terreno historial",
            address="Dirección historial",
        )

        self.other_terrain = Terrain.objects.create(
            name="Otro terreno historial",
            address="Otra dirección",
        )

        self.access_point = AccessPoint.objects.create(
            name="Acceso historial",
            point_type="PORTON",
            terrain=self.terrain,
        )

        self.other_access_point = AccessPoint.objects.create(
            name="Otro acceso",
            point_type="PUERTA",
            terrain=self.other_terrain,
        )

        self.credential = Credential.objects.create(
            uid_rfid="RFID-HISTORY-001",
            person=self.person,
        )

        self.other_credential = Credential.objects.create(
            uid_rfid="RFID-HISTORY-002",
            person=self.other_person,
        )

        self.record = AccessRecord.objects.create(
            medium=AccessRecord.Medium.RFID,
            result=AccessRecord.Result.ALLOWED,
            description="Acceso autorizado",
            uid_received=self.credential.uid_rfid,
            access_point=self.access_point,
            credential=self.credential,
        )

        self.other_record = AccessRecord.objects.create(
            medium=AccessRecord.Medium.APP,
            result=AccessRecord.Result.DENIED,
            description="Acceso denegado",
            uid_received=self.other_credential.uid_rfid,
            access_point=self.other_access_point,
            credential=self.other_credential,
        )

        self.history_url = reverse("access-record-list")

    def test_filtrar_por_persona(self):
        response = self.client.get(
            self.history_url,
            {"person": self.person.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["id_access_record"],
            self.record.pk,
        )

    def test_filtrar_por_terreno(self):
        response = self.client.get(
            self.history_url,
            {"terrain": self.terrain.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_por_punto_de_acceso(self):
        response = self.client.get(
            self.history_url,
            {"access_point": self.access_point.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)

    def test_filtrar_por_resultado(self):
        response = self.client.get(
            self.history_url,
            {"result": AccessRecord.Result.DENIED},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["result"],
            AccessRecord.Result.DENIED,
        )

    def test_filtrar_por_medio(self):
        response = self.client.get(
            self.history_url,
            {"medium": AccessRecord.Medium.APP},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["medium"],
            AccessRecord.Medium.APP,
        )

    def test_filtrar_por_rango_de_fechas(self):
        today = timezone.localdate()

        response = self.client.get(
            self.history_url,
            {
                "date_from": today.isoformat(),
                "date_to": today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 2)

    def test_rango_de_fechas_invertido_responde_400(self):
        today = timezone.localdate()

        response = self.client.get(
            self.history_url,
            {
                "date_from": (
                    today + timedelta(days=5)
                ).isoformat(),
                "date_to": today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 400)

    def test_valor_de_resultado_invalido_responde_400(self):
        response = self.client.get(
            self.history_url,
            {"result": "RESULTADO_INCORRECTO"},
        )

        self.assertEqual(response.status_code, 400)

    def test_combinar_filtros(self):
        today = timezone.localdate()

        response = self.client.get(
            self.history_url,
            {
                "person": self.person.pk,
                "terrain": self.terrain.pk,
                "result": AccessRecord.Result.ALLOWED,
                "medium": AccessRecord.Medium.RFID,
                "date_from": today.isoformat(),
                "date_to": today.isoformat(),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(
            response.data["results"][0]["id_access_record"],
            self.record.pk,
        )
