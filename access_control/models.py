
from django.db import models


class Terreno(models.Model):
    id_terreno = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    direccion = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, default="ACTIVO")

    class Meta:
        db_table = "terreno"
        verbose_name = "Terreno"
        verbose_name_plural = "Terrenos"

    def __str__(self):
        return self.nombre


class Vivienda(models.Model):
    id_vivienda = models.AutoField(primary_key=True)
    n_identificador = models.CharField(max_length=50)
    tipo = models.CharField(max_length=30)
    direccion = models.CharField(max_length=200)
    estado = models.CharField(max_length=20, default="ACTIVO")

    terreno = models.ForeignKey(
        Terreno,
        on_delete=models.PROTECT,
        related_name="viviendas",
        db_column="id_terreno"
    )

    class Meta:
        db_table = "vivienda"
        verbose_name = "Vivienda"
        verbose_name_plural = "Viviendas"
        constraints = [
            models.UniqueConstraint(
                fields=["terreno", "n_identificador"],
                name="uq_vivienda_terreno_identificador"
            )
        ]

    def __str__(self):
        return f"{self.tipo} {self.n_identificador}"

#app
class PuntoAcceso(models.Model):
    id_punto_acceso = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    tipo = models.CharField(max_length=50)
    estado = models.CharField(max_length=20, default="ACTIVO")

    terreno = models.ForeignKey(
        Terreno,
        on_delete=models.PROTECT,
        related_name="puntos_acceso",
        db_column="id_terreno"
    )

    class Meta:
        db_table = "punto_acceso"
        verbose_name = "Punto de acceso"
        verbose_name_plural = "Puntos de acceso"

    def __str__(self):
        return f"{self.nombre} - {self.terreno.nombre}"
