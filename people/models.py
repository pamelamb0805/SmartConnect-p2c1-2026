
from django.db import models


class Person(models.Model):
    id_person = models.AutoField(
        primary_key=True,
        db_column="id_persona",
        verbose_name="ID de persona",
    )

    rut = models.CharField(
        max_length=20,
        verbose_name="RUT",
    )

    first_name = models.CharField(
        max_length=100,
        db_column="nombre",
        verbose_name="Nombre",
    )

    last_name = models.CharField(
        max_length=100,
        db_column="apellido",
        verbose_name="Apellido",
    )

    email = models.EmailField(
        max_length=254,
        db_column="correo",
        blank=True,
        verbose_name="Correo electrónico",
    )

    phone = models.CharField(
        max_length=30,
        db_column="telefono",
        blank=True,
        verbose_name="Teléfono",
    )

    class Meta:
        db_table = "persona"
        verbose_name = "Persona"
        verbose_name_plural = "Personas"
        ordering = ["last_name", "first_name"]

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.rut})"
