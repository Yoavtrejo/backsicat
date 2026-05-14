from rest_framework import serializers


class ExplicarElementoSerializer(serializers.Serializer):
    nombre_capa = serializers.CharField(required=False, allow_blank=True, max_length=200)
    categoria = serializers.CharField(required=False, allow_blank=True, max_length=100)
    properties = serializers.JSONField(required=True)

    def validate_properties(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("properties debe ser un objeto.")
        if len(value) == 0:
            raise serializers.ValidationError("properties no puede estar vacío.")
        if len(value) > 80:
            raise serializers.ValidationError("Demasiados atributos (máx. 80).")
        return value


class GenerarInformeSerializer(serializers.Serializer):
    estado = serializers.CharField(required=False, allow_blank=True, max_length=80)
    municipio = serializers.CharField(required=False, allow_blank=True, max_length=120)
    proyecto_id = serializers.IntegerField(required=False)
    capa_ids = serializers.ListField(
        child=serializers.IntegerField(min_value=1),
        required=False,
        allow_empty=True,
    )
    tono = serializers.ChoiceField(
        choices=["tecnico", "ejecutivo"],
        required=False,
        default="ejecutivo",
    )
