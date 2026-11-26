
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from rest_framework.test import APIClient

from people.models import Person
from infrastructure.models import Terrain, Dwelling, AccessPoint

from .models import (
    Role,
    PersonRole,
    Credential,
    AccessRecord,
)
from .permissions import user_can_access_dwelling

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


class AuthorizationSecurityTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.client = APIClient()

        self.user = User.objects.create_user(
            username="usuario_seguridad",
            email="seguridad@test.cl",
            password="TestPassword123!",
        )

        self.person = Person.objects.create(
            user=self.user,
            rut="44444444-4",
            first_name="Usuario",
            last_name="Seguridad",
        )

        self.terrain = Terrain.objects.create(
            name="Terreno seguridad",
            address="Dirección seguridad",
            status="ACTIVO",
        )

        self.dwelling_one = Dwelling.objects.create(
            identifier_number="CASA-01",
            dwelling_type="CASA",
            address="Casa 1",
            terrain=self.terrain,
            status="ACTIVO",
        )

        self.dwelling_two = Dwelling.objects.create(
            identifier_number="CASA-02",
            dwelling_type="CASA",
            address="Casa 2",
            terrain=self.terrain,
            status="ACTIVO",
        )

        self.role = Role.objects.create(
            name="Rol vivienda seguridad",
            description="Acceso a una vivienda específica",
            scope=Role.Scope.DWELLING,
            status=Role.Status.ACTIVE,
        )

        self.assignment = PersonRole.objects.create(
            person=self.person,
            role=self.role,
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            dwelling=self.dwelling_one,
        )

    def test_sin_token_responde_401(self):
        response = self.client.get(reverse("terreno-list"))

        self.assertEqual(response.status_code, 401)

    def test_usuario_sin_permiso_no_puede_crear_terreno(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            reverse("terreno-list"),
            {
                "name": "Terreno no autorizado",
                "address": "Dirección no autorizada",
                "status": "ACTIVO",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(
            Terrain.objects.filter(
                name="Terreno no autorizado"
            ).exists()
        )

    def test_usuario_no_accede_a_otra_vivienda_del_mismo_terreno(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(
            reverse(
                "vivienda-detail",
                kwargs={"pk": self.dwelling_two.pk},
            )
        )

        self.assertEqual(response.status_code, 403)

    def test_listado_solo_muestra_vivienda_autorizada(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.get(reverse("vivienda-list"))

        self.assertEqual(response.status_code, 200)

        ids = [
            item["id_dwelling"]
            for item in response.data
        ]

        self.assertIn(self.dwelling_one.pk, ids)
        self.assertNotIn(self.dwelling_two.pk, ids)

    def test_usuario_no_puede_editar_vivienda_ajena(self):
        self.client.force_authenticate(user=self.user)

        response = self.client.patch(
            reverse(
                "vivienda-detail",
                kwargs={"pk": self.dwelling_two.pk},
            ),
            {"address": "Dirección modificada"},
            format="json",
        )

        self.assertEqual(response.status_code, 403)

        self.dwelling_two.refresh_from_db()
        self.assertEqual(self.dwelling_two.address, "Casa 2")

    def test_asignacion_vivienda_no_autoriza_otras_viviendas(self):
        self.client.force_authenticate(user=self.user)

        self.assertTrue(
            user_can_access_dwelling(
                self.user,
                self.dwelling_one.pk,
            )
        )

        self.assertFalse(
            user_can_access_dwelling(
                self.user,
                self.dwelling_two.pk,
            )
        )


class RFIDIntegrityTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.user = User.objects.create_superuser(
            username="admin_integridad",
            email="integridad@test.cl",
            password="TestPassword123!",
        )

        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

        self.person = Person.objects.create(
            rut="55555555-5",
            first_name="Persona",
            last_name="Integridad",
        )

        self.terrain = Terrain.objects.create(
            name="Terreno integridad",
            address="Dirección integridad",
            status="ACTIVO",
        )

        self.point = AccessPoint.objects.create(
            name="Acceso integridad",
            point_type="PORTON",
            status="ACTIVO",
            terrain=self.terrain,
        )

        self.role = Role.objects.create(
            name="Rol integridad",
            description="Prueba de integridad",
            scope=Role.Scope.TERRAIN,
            status=Role.Status.ACTIVE,
        )

        self.credential = Credential.objects.create(
            uid_rfid="RFID-INTEGRIDAD",
            status=Credential.Status.BLOCKED,
            person=self.person,
        )

        self.assignment = PersonRole.objects.create(
            person=self.person,
            role=self.role,
            start_date=timezone.localdate() - timedelta(days=1),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            terrain=self.terrain,
        )

    def test_rechazo_rfid_no_modifica_estados_de_la_base_de_datos(self):
        credential_status = self.credential.status
        assignment_status = self.assignment.status
        role_status = self.role.status
        terrain_status = self.terrain.status

        response = self.client.post(
            reverse("check-access"),
            {
                "uid_rfid": self.credential.uid_rfid,
                "access_point_id": self.point.pk,
                "medium": "RFID",
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.data["autorizado"])

        self.credential.refresh_from_db()
        self.assignment.refresh_from_db()
        self.role.refresh_from_db()
        self.terrain.refresh_from_db()

        self.assertEqual(self.credential.status, credential_status)
        self.assertEqual(self.assignment.status, assignment_status)
        self.assertEqual(self.role.status, role_status)
        self.assertEqual(self.terrain.status, terrain_status)

        record = AccessRecord.objects.get()

        self.assertEqual(
            record.result,
            AccessRecord.Result.DENIED,
        )
        self.assertEqual(
            record.uid_received,
            self.credential.uid_rfid,
        )
