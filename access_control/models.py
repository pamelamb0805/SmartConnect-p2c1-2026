
from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import Q


class Role(models.Model):
    class Scope(models.TextChoices):
        TERRAIN = "TERRENO", "Terreno"
        DWELLING = "VIVIENDA", "Vivienda"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVO", "Activo"
        INACTIVE = "INACTIVO", "Inactivo"

    id_role = models.AutoField(
        primary_key=True,
        db_column="id_rol",
        verbose_name="ID de rol",
    )
    name = models.CharField(
        max_length=80,
        db_column="nombre",
        unique=True,
        verbose_name="Nombre",
    )
    description = models.TextField(
        db_column="descripcion",
        blank=True,
        verbose_name="Descripción",
    )
    scope = models.CharField(
        max_length=20,
        db_column="ambito",
        choices=Scope.choices,
        verbose_name="Ámbito",
    )
    status = models.CharField(
        max_length=20,
        db_column="estado",
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )

    class Meta:
        db_table = "rol"
        verbose_name = "Rol"
        verbose_name_plural = "Roles"
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.get_scope_display()})"


class PersonRole(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVO", "Activo"
        INACTIVE = "INACTIVO", "Inactivo"

    id_person_role = models.AutoField(
        primary_key=True,
        db_column="id_persona_rol",
        verbose_name="ID de relación persona-rol",
    )
    person = models.ForeignKey(
        "people.Person",
        on_delete=models.PROTECT,
        related_name="role_assignments",
        db_column="id_persona",
        verbose_name="Persona",
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.PROTECT,
        related_name="person_assignments",
        db_column="id_rol",
        verbose_name="Rol",
    )
    start_date = models.DateField(
        db_column="fecha_inicio",
        verbose_name="Fecha de inicio",
    )
    end_date = models.DateField(
        db_column="fecha_fin",
        null=True,
        blank=True,
        verbose_name="Fecha de término",
    )
    status = models.CharField(
        max_length=20,
        db_column="estado",
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )
    terrain = models.ForeignKey(
        "infrastructure.Terrain",
        on_delete=models.PROTECT,
        related_name="person_role_assignments",
        db_column="id_terreno",
        null=True,
        blank=True,
        verbose_name="Terreno",
    )
    dwelling = models.ForeignKey(
        "infrastructure.Dwelling",
        on_delete=models.PROTECT,
        related_name="person_role_assignments",
        db_column="id_vivienda",
        null=True,
        blank=True,
        verbose_name="Vivienda",
    )

    class Meta:
        db_table = "persona_rol"
        verbose_name = "Asignación de rol"
        verbose_name_plural = "Asignaciones de roles"
        ordering = ["-start_date"]
        class Meta:
            db_table = "persona_rol"
            verbose_name = "Asignación de rol"
            verbose_name_plural = "Asignaciones de roles"
            ordering = ["-start_date"]

    def clean(self):
        errors = {}

        if self.end_date and self.start_date and self.end_date < self.start_date:
            errors["end_date"] = "La fecha de término no puede ser anterior a la fecha de inicio."

        if self.role_id:
            if self.role.scope == Role.Scope.TERRAIN:
                if not self.terrain_id or self.dwelling_id:
                    errors["terrain"] = "Este rol debe estar asociado a un terreno y no a una vivienda."
            elif self.role.scope == Role.Scope.DWELLING:
                if not self.dwelling_id or self.terrain_id:
                    errors["dwelling"] = "Este rol debe estar asociado a una vivienda y no a un terreno."

        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.person} - {self.role}"


class Credential(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVO", "Activa"
        INACTIVE = "INACTIVO", "Inactiva"
        BLOCKED = "BLOQUEADO", "Bloqueada"

    id_credential = models.AutoField(
        primary_key=True,
        db_column="id_credencial",
        verbose_name="ID de credencial",
    )
    uid_rfid = models.CharField(
        max_length=100,
        db_column="uid_rfid",
        unique=True,
        verbose_name="UID RFID",
    )
    status = models.CharField(
        max_length=20,
        db_column="estado",
        choices=Status.choices,
        default=Status.ACTIVE,
        verbose_name="Estado",
    )
    person = models.ForeignKey(
        "people.Person",
        on_delete=models.PROTECT,
        related_name="credentials",
        db_column="id_persona",
        verbose_name="Titular",
    )

    class Meta:
        db_table = "credencial"
        verbose_name = "Credencial"
        verbose_name_plural = "Credenciales"
        ordering = ["uid_rfid"]

    def __str__(self):
        return f"{self.uid_rfid} - {self.person}"


class AccessRecord(models.Model):
    class Medium(models.TextChoices):
        RFID = "RFID", "RFID"
        APP = "APP", "Aplicación"
        OTHER = "OTRO", "Otro"

    class Result(models.TextChoices):
        ALLOWED = "PERMITIDO", "Permitido"
        DENIED = "DENEGADO", "Denegado"

    id_access_record = models.AutoField(
        primary_key=True,
        db_column="id_registro_acceso",
        verbose_name="ID de registro",
    )
    date_time = models.DateTimeField(
        db_column="fecha_hora",
        auto_now_add=True,
        verbose_name="Fecha y hora",
    )
    medium = models.CharField(
        max_length=20,
        db_column="medio",
        choices=Medium.choices,
        verbose_name="Medio",
    )
    result = models.CharField(
        max_length=20,
        db_column="resultado",
        choices=Result.choices,
        verbose_name="Resultado",
    )
    description = models.TextField(
        db_column="descripcion",
        blank=True,
        verbose_name="Descripción",
    )
    uid_received = models.CharField(
        max_length=100,
        db_column="uid_recibido",
        blank=True,
        verbose_name="UID recibido",
    )
    access_point = models.ForeignKey(
        "infrastructure.AccessPoint",
        on_delete=models.PROTECT,
        related_name="access_records",
        db_column="id_punto_acceso",
        verbose_name="Punto de acceso",
    )
    credential = models.ForeignKey(
        Credential,
        on_delete=models.SET_NULL,
        related_name="access_records",
        db_column="id_credencial",
        null=True,
        blank=True,
        verbose_name="Credencial identificada",
    )

    class Meta:
        db_table = "registro_acceso"
        verbose_name = "Registro de acceso"
        verbose_name_plural = "Registros de acceso"
        ordering = ["-date_time"]

    def clean(self):
        if self.credential_id and self.uid_received:
            if self.credential.uid_rfid != self.uid_received:
                raise ValidationError({
                    "uid_received": "El UID recibido no coincide con la credencial seleccionada."
                })

    def __str__(self):
        return f"{self.date_time} - {self.result} - {self.access_point}"
