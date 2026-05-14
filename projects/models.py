import uuid
from django.db import models
from django.contrib.auth.models import User


class Proyecto(models.Model):
    """Modelo para gestionar proyectos geográficos."""

    CATEGORIA_CHOICES = [
        ('ALTIMETRIA', 'Altimetría'),
        ('CATASTRO', 'Catastro'),
        ('EQUIPAMIENTO', 'Equipamiento Urbano'),
        ('ESTRUCTURA', 'Estructura Urbana'),
        ('HIDROLOGIA', 'Hidrología'),
        ('INFRAESTRUCTURA', 'Infraestructura'),
        ('TOPOGRAFIA', 'Topografía'),
        ('USOS_PREDIO', 'Usos de Predio'),
        ('VEGETACION', 'Vegetación'),
        ('VIAS', 'Vías'),
        ('OTROS', 'Otros'),
    ]

    ESCALA_CHOICES = [
        ('1:500', '1:500'),
        ('1:1000', '1:1,000'),
        ('1:2000', '1:2,000'),
        ('1:5000', '1:5,000'),
        ('1:10000', '1:10,000'),
        ('1:20000', '1:20,000'),
        ('1:50000', '1:50,000'),
        ('OTRA', 'Otra'),
    ]

    # --- Folio automático ---
    folio = models.CharField(
        max_length=30,
        unique=True,
        editable=False,
        help_text="Folio generado automáticamente (ej: PROY-2026-0001)"
    )

    # --- Campos del formulario ---
    nombre_proyecto = models.CharField(max_length=200, help_text="Nombre descriptivo del proyecto")
    anio = models.PositiveIntegerField(help_text="Año del proyecto")
    estado = models.CharField(max_length=50, help_text="Estado de la república")
    municipio = models.CharField(max_length=100, help_text="Municipio")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    tipo_escala = models.CharField(max_length=10, choices=ESCALA_CHOICES)

    # --- Fases y avance ---
    fases = models.JSONField(
        default=list,
        blank=True,
        help_text="Lista de fases del proyecto. Ej: [{\"nombre\": \"Levantamiento\", \"completada\": false}]"
    )
    avance = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0,
        help_text="Porcentaje de avance del proyecto (0.00 - 100.00)"
    )

    # --- Metadatos ---
    creado_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Proyecto"
        verbose_name_plural = "Proyectos"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['estado', 'municipio', 'categoria']),
            models.Index(fields=['folio']),
        ]

    def save(self, *args, **kwargs):
        """Genera el folio automáticamente al crear un proyecto."""
        if not self.folio:
            anio = self.anio or 2026
            # Contar cuántos proyectos ya existen para ese año
            count = Proyecto.objects.filter(anio=anio).count() + 1
            self.folio = f"PROY-{anio}-{count:04d}"

            # Asegurar unicidad en caso de concurrencia
            while Proyecto.objects.filter(folio=self.folio).exists():
                count += 1
                self.folio = f"PROY-{anio}-{count:04d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.folio} - {self.nombre_proyecto}"
