
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from people.models import Person
from infrastructure.models import Terrain, AccessPoint, Dwelling

from .models import Role, PersonRole, Credential, AccessRecord
from .services import evaluate_and_register_access


class AccessControlServiceTests(TestCase):
    """Pruebas del servicio que evalúa y registra intentos de acceso."""

    def setUp(self):
        self.today = timezone.localdate()

        self.person = Person.objects.create(
            rut="11111111-1",
            first_name="Persona",
            last_name="Prueba",
            email="persona@example.com",
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
            name="Propietario de prueba",
            description="Rol para pruebas automatizadas",
            scope=Role.Scope.TERRAIN,
            status=Role.Status.ACTIVE,
        )

        self.assignment = PersonRole.objects.create(
            person=self.person,
            role=self.role,
            start_date=self.today - timedelta(days=10),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            terrain=self.terrain,
            dwelling=None,
        )

        self.credential = Credential.objects.create(
            uid_rfid="UID-TEST-001",
            status=Credential.Status.ACTIVE,
            person=self.person,
        )

    def evaluate(self, uid="UID-TEST-001", access_point=None):
        return evaluate_and_register_access(
            uid_rfid=uid,
            access_point=access_point or self.access_point,
            medium=AccessRecord.Medium.RFID,
        )

    def test_active_credential_and_valid_role_allow_access(self):
        result = self.evaluate()

        self.assertTrue(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.ALLOWED,
        )
        self.assertIsNotNone(result["record"])
        self.assertEqual(AccessRecord.objects.count(), 1)

    def test_unknown_uid_denies_and_records_received_uid(self):
        result = self.evaluate(uid="UID-DESCONOCIDO")

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )
        self.assertIsNone(result["credential"])
        self.assertEqual(
            result["record"].uid_received,
            "UID-DESCONOCIDO",
        )
        self.assertEqual(AccessRecord.objects.count(), 1)

    def test_blocked_credential_denies_access(self):
        self.credential.status = Credential.Status.BLOCKED
        self.credential.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )
        self.assertIn("inactiva o bloqueada", result["description"])

    def test_inactive_credential_denies_access(self):
        self.credential.status = Credential.Status.INACTIVE
        self.credential.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )

    def test_expired_role_assignment_denies_access(self):
        self.assignment.end_date = self.today - timedelta(days=1)
        self.assignment.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )

    def test_inactive_role_denies_access(self):
        self.role.status = Role.Status.INACTIVE
        self.role.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )

    def test_inactive_access_point_denies_access(self):
        self.access_point.status = "INACTIVO"
        self.access_point.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertIn("punto de acceso está inactivo", result["description"])

    def test_inactive_terrain_denies_access(self):
        self.terrain.status = "INACTIVO"
        self.terrain.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertIn("terreno está inactivo", result["description"])

    def test_person_without_assignment_denies_access(self):
        self.assignment.delete()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )

    def test_future_assignment_does_not_allow_access(self):
        self.assignment.start_date = self.today + timedelta(days=1)
        self.assignment.save()

        result = self.evaluate()

        self.assertFalse(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.DENIED,
        )

    def test_access_by_dwelling_role_in_same_terrain_is_allowed(self):
        self.assignment.delete()

        dwelling = Dwelling.objects.create(
            identifier_number="CASA-01",
            dwelling_type="CASA",
            address="Dirección casa 1",
            status="ACTIVO",
            terrain=self.terrain,
        )

        dwelling_role = Role.objects.create(
            name="Residente de prueba",
            description="Rol asociado a vivienda",
            scope=Role.Scope.DWELLING,
            status=Role.Status.ACTIVE,
        )

        PersonRole.objects.create(
            person=self.person,
            role=dwelling_role,
            start_date=self.today - timedelta(days=1),
            end_date=None,
            status=PersonRole.Status.ACTIVE,
            terrain=None,
            dwelling=dwelling,
        )

        result = self.evaluate()

        self.assertTrue(result["allowed"])
        self.assertEqual(
            result["result"],
            AccessRecord.Result.ALLOWED,
        )

    def test_every_attempt_is_registered(self):
        self.evaluate()
        self.evaluate(uid="UID-DESCONOCIDO")

        self.assertEqual(AccessRecord.objects.count(), 2)

        results = set(
            AccessRecord.objects.values_list("result", flat=True)
        )

        self.assertIn(AccessRecord.Result.ALLOWED, results)
        self.assertIn(AccessRecord.Result.DENIED, results)
