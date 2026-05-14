from rest_framework import serializers
from .models import CapaGeografica

class CapaGeograficaSerializer(serializers.ModelSerializer):
    class Meta:
        model = CapaGeografica
        fields = [
            'id', 'nombre_capa', 'estado', 'municipio', 
            'categoria', 'tipo_geometria', 'datos_normalizados', 
            'fecha_subida'
        ]