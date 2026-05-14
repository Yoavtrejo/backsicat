from django.db import models
from django.contrib.auth.models import User

class CapaGeografica(models.Model):
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
        ('IZUCAR', 'Izúcar (Proyectos Especiales)'),
        ('OTROS', 'Otros'),
    ]

    GEOMETRIA_CHOICES = [
        ('PUNTOS', 'Punto / MultiPunto'),
        ('LINEAS', 'Línea / MultiLineString'),
        ('POLIGONOS', 'Polígono / MultiPolígono'),
    ]

    nombre_capa = models.CharField(max_length=150, help_text="Ej: Curvas de nivel maestras")
    estado = models.CharField(max_length=50, help_text="Se selecciona desde el formulario")
    municipio = models.CharField(max_length=100, help_text="Se selecciona desde el formulario")
    categoria = models.CharField(max_length=20, choices=CATEGORIA_CHOICES)
    tipo_geometria = models.CharField(max_length=20, choices=GEOMETRIA_CHOICES)

    archivo_original = models.FileField(upload_to='geojsons/originales/%Y/%m/')
    
    datos_normalizados = models.JSONField(help_text="GeoJSON con atributos estandarizados y limpios")

    subido_por = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    fecha_subida = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Capa Geográfica"
        verbose_name_plural = "Capas Geográficas"
        indexes = [
            models.Index(fields=['estado', 'municipio', 'categoria']),
        ]

    def __str__(self):
        return f"{self.nombre_capa} - {self.categoria} ({self.municipio, self.estado})"