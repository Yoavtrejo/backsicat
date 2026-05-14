from rest_framework import serializers
from .models import Proyecto


class ProyectoSerializer(serializers.ModelSerializer):
    creado_por_nombre = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Proyecto
        fields = [
            'id', 'folio', 'nombre_proyecto', 'anio',
            'estado', 'municipio', 'categoria', 'tipo_escala',
            'fases', 'avance',
            'creado_por', 'creado_por_nombre',
            'fecha_creacion', 'fecha_actualizacion',
        ]
        read_only_fields = ['id', 'folio', 'creado_por', 'fecha_creacion', 'fecha_actualizacion']

    def get_creado_por_nombre(self, obj):
        if obj.creado_por:
            return f"{obj.creado_por.first_name} {obj.creado_por.last_name}".strip() or obj.creado_por.username
        return None

    def validate_avance(self, value):
        """Asegura que el avance esté entre 0 y 100."""
        if value < 0 or value > 100:
            raise serializers.ValidationError("El avance debe estar entre 0.00 y 100.00.")
        return value

    def validate_fases(self, value):
        """Valida que fases sea una lista de objetos con 'nombre' y 'completada'."""
        if not isinstance(value, list):
            raise serializers.ValidationError("Las fases deben ser una lista.")
        for i, fase in enumerate(value):
            if not isinstance(fase, dict):
                raise serializers.ValidationError(f"La fase en posición {i} debe ser un objeto.")
            if 'nombre' not in fase:
                raise serializers.ValidationError(f"La fase en posición {i} requiere el campo 'nombre'.")
            if 'completada' not in fase:
                raise serializers.ValidationError(f"La fase en posición {i} requiere el campo 'completada'.")
        return value

