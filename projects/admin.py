from django.contrib import admin
from .models import Proyecto


@admin.register(Proyecto)
class ProyectoAdmin(admin.ModelAdmin):
    list_display = ('folio', 'nombre_proyecto', 'anio', 'estado', 'municipio', 'categoria', 'tipo_escala', 'avance', 'fecha_creacion')
    list_filter = ('categoria', 'tipo_escala', 'estado', 'anio')
    search_fields = ('folio', 'nombre_proyecto', 'municipio')
    readonly_fields = ('folio', 'fecha_creacion', 'fecha_actualizacion')
