
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from infrastructure.models import AccessPoint
from .models import (
    Role,
    PersonRole,
    Credential,
    AccessRecord,
)


@transaction.atomic
def evaluate_and_register_access(uid_rfid, access_point, medium):
    """
    Evalúa un intento de acceso y registra siempre el resultado.

    Un intento con UID desconocido también queda registrado,
    conservando el UID recibido.
    """

    uid_rfid = uid_rfid.strip()
    today = timezone.localdate()

    credential = (
        Credential.objects
        .select_related("person")
        .filter(uid_rfid=uid_rfid)
        .first()
    )

    allowed = False
    reason = ""
    
    if credential is None:
        reason = "Credencial desconocida."

    elif credential.status != Credential.Status.ACTIVE:
        reason = "La credencial está inactiva o bloqueada."

    elif access_point.status != "ACTIVO":
        reason = "El punto de acceso está inactivo."

    elif access_point.terrain.status != "ACTIVO":
        reason = "El terreno está inactivo."

    else:
        assignments = PersonRole.objects.filter(
            person_id=credential.person_id,
            status=PersonRole.Status.ACTIVE,
            role__status=Role.Status.ACTIVE,
            start_date__lte=today,
        ).filter(
            Q(end_date__isnull=True) |
            Q(end_date__gte=today)
        ).filter(
            Q(
                role__scope=Role.Scope.TERRAIN,
                terrain_id=access_point.terrain_id,
                dwelling__isnull=True,
            ) |
            Q(
                role__scope=Role.Scope.DWELLING,
                dwelling__terrain_id=access_point.terrain_id,
                dwelling__status="ACTIVO",
                terrain__isnull=True,
            )
        )

        if assignments.exists():
            allowed = True
            reason = "Acceso autorizado por asignación de rol vigente."
        else:
            reason = (
                "La persona no tiene una asignación de rol "
                "activa y vigente para este terreno."
            )

    record = AccessRecord.objects.create(
        medium=medium,
        result=(
            AccessRecord.Result.ALLOWED
            if allowed
            else AccessRecord.Result.DENIED
        ),
        description=reason,
        uid_received=uid_rfid,
        access_point=access_point,
        credential=credential,
    )

    return {
        "allowed": allowed,
        "result": record.result,
        "description": reason,
        "record": record,
        "credential": credential,
    }
