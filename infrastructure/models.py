
from django.db import models


class Terrain(models.Model):
    id_terrain = models.AutoField(
        primary_key=True,
        db_column="id_terreno",
        verbose_name="ID de terreno",
    )

    name = models.CharField(
        max_length=100,
        db_column="nombre",
        verbose_name="Nombre",
    )

    address = models.CharField(
        max_length=200,
        db_column="direccion",
        verbose_name="Dirección",
    )

    status = models.CharField(
        max_length=20,
        db_column="estado",
        default="ACTIVO",
        verbose_name="Estado",
    )

    class Meta:
        db_table = "terreno"
        verbose_name = "Terreno"
        verbose_name_plural = "Terrenos"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Dwelling(models.Model):
    id_dwelling = models.AutoField(
        primary_key=True,
        db_column="id_vivienda",
        verbose_name="ID de vivienda",
    )

    identifier_number = models.CharField(
        max_length=50,
        db_column="n_identificador",
        verbose_name="Número identificador",
    )

    dwelling_type = models.CharField(
        max_length=30,
        db_column="tipo",
        verbose_name="Tipo de vivienda",
    )

    address = models.CharField(
        max_length=200,
        db_column="direccion",
        verbose_name="Dirección",
    )

    status = models.CharField(
        max_length=20,
        db_column="estado",
        default="ACTIVO",
        verbose_name="Estado",
    )

    terrain = models.ForeignKey(
        Terrain,
        on_delete=models.PROTECT,
        related_name="dwellings",
        db_column="id_terreno",
        verbose_name="Terreno",
    )

    class Meta:
        db_table = "vivienda"
        verbose_name = "Vivienda"
        verbose_name_plural = "Viviendas"
        ordering = ["terrain", "identifier_number"]
        constraints = [
            models.UniqueConstraint(
                fields=["terrain", "identifier_number"],
                name="uq_vivienda_terreno_identificador",
            )
        ]

    def __str__(self):
        return f"{self.dwelling_type} {self.identifier_number}"


class AccessPoint(models.Model):
    id_access_point = models.AutoField(
        primary_key=True,
        db_column="id_punto_acceso",
        verbose_name="ID de punto de acceso",
    )

    name = models.CharField(
        max_length=100,
        db_column="nombre",
        verbose_name="Nombre",
    )

    point_type = models.CharField(
        max_length=50,
        db_column="tipo",
        verbose_name="Tipo",
    )

    status = models.CharField(
        max_length=20,
        db_column="estado",
        default="ACTIVO",
        verbose_name="Estado",
    )

    terrain = models.ForeignKey(
        Terrain,
        on_delete=models.PROTECT,
        related_name="access_points",
        db_column="id_terreno",
        verbose_name="Terreno",
    )

    class Meta:
        db_table = "punto_acceso"
        verbose_name = "Punto de acceso"
        verbose_name_plural = "Puntos de acceso"
        ordering = ["terrain", "name"]

    def __str__(self):
        return f"{self.name} - {self.terrain.name}"
