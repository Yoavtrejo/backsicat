import json
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from .models import CapaGeografica
from .serializers import CapaGeograficaSerializer

class SubirCapaNormalizadaView(APIView):
    parser_classes = (MultiPartParser, FormParser)

    DICCIONARIO_TRADUCCION = {
        'Z': 'elevacion_m',
        'z_pred': 'elevacion_m',
        'z_constriccion': 'elevacion_m',
        'DFX_ELEVATION': 'elevacion_m',
        'DXF_Elevation': 'elevacion_m',
        'Shape_Area': 'area_m2',
        'Shape_Length': 'longitud_o_perimetro_m',
        'OBJECTID': 'arcgis_id',
        'CATEGORIA': 'categoria_origen',
        'CODIGO': 'codigo_elemento',
        'ELEMENTO': 'tipo_elemento',
        'Objeto': 'tipo_elemento',
        'Tipo': 'clasificacion',
        'NN': 'nombre_identificador',
        'OneWay': 'sentido_vialidad',
        'Etiqueta': 'etiqueta_mapa',
        'Espacio': 'nombre_espacio',
        'Shape_Area': 'area_m2',
        'Shape_Length': 'longitud_o_perimetro_m',
        'area_pred': 'area_m2', 
        'OBJECTID': 'arcgis_id',
        'CATEGORIA': 'categoria_origen',
        'CODIGO': 'codigo_elemento',
        'ELEMENTO': 'tipo_elemento',
        'Objeto': 'tipo_elemento',
        'Tipo': 'clasificacion',
        'NN': 'nombre_identificador',
        'OneWay': 'sentido_vialidad',
        'Etiqueta': 'etiqueta_mapa',
        'Espacio': 'nombre_espacio',
    }

    def get(self, request, pk=None):
        if pk:
            try:
                capa = CapaGeografica.objects.get(pk=pk)
                return Response({
                    "id": capa.id,
                    "nombre_capa": capa.nombre_capa,
                    "categoria": capa.categoria,
                    "datos_normalizados": capa.datos_normalizados
                }, status=status.HTTP_200_OK)
            except CapaGeografica.DoesNotExist:
                return Response({"error": "Capa no encontrada"}, status=status.HTTP_404_NOT_FOUND)
        
        from django.db.models import Q

        estado_query = request.query_params.get('estado')
        municipio_query = request.query_params.get('municipio')
        
        queryset = CapaGeografica.objects.all()
        
        def variaciones(texto):
            if not texto: return []
            t_sin = texto.replace('á', 'a').replace('é', 'e').replace('í', 'i').replace('ó', 'o').replace('ú', 'u').replace('Á', 'A').replace('É', 'E').replace('Í', 'I').replace('Ó', 'O').replace('Ú', 'U')
            return [texto, t_sin, texto.upper(), t_sin.upper()]
        
        if estado_query:
            vars_estado = variaciones(estado_query)
            q_estado = Q()
            for v in vars_estado:
                q_estado |= Q(estado__icontains=v)
            queryset = queryset.filter(q_estado)
            
        if municipio_query:
            vars_muni = variaciones(municipio_query)
            q_muni = Q()
            for v in vars_muni:
                q_muni |= Q(municipio__icontains=v)
            queryset = queryset.filter(q_muni)
            
        capas = queryset.values('id', 'nombre_capa', 'estado', 'municipio', 'categoria')
        return Response(list(capas), status=status.HTTP_200_OK)


    parser_classes = (MultiPartParser, FormParser)

    DICCIONARIO_TRADUCCION = {
        'Z': 'elevacion_m',
        'DFX_ELEVATION': 'elevacion_m',
        'DXF_Elevation': 'elevacion_m',
        
        'Shape_Area': 'area_m2',
        'Shape_Length': 'longitud_o_perimetro_m',
        
        'OBJECTID': 'arcgis_id',
        'CATEGORIA': 'categoria_origen',
        'CODIGO': 'codigo_elemento',
        'ELEMENTO': 'tipo_elemento',
        'Objeto': 'tipo_elemento',
        'Tipo': 'clasificacion',
        'NN': 'nombre_identificador',
        'OneWay': 'sentido_vialidad',
        'Etiqueta': 'etiqueta_mapa',
        'Espacio': 'nombre_espacio',
    }

    def post(self, request, *args, **kwargs):
        try:
            archivo_subido = request.FILES.get('archivo_original')
            if not archivo_subido:
                return Response({"error": "No se envió ningún archivo GeoJSON."}, status=status.HTTP_400_BAD_REQUEST)
            datos_geojson = json.load(archivo_subido)

            for feature in datos_geojson.get('features', []):
                propiedades_viejas = feature.get('properties', {})
                propiedades_limpias = {}

                for clave_vieja, valor in propiedades_viejas.items():
                    if clave_vieja in self.DICCIONARIO_TRADUCCION:
                        clave_nueva = self.DICCIONARIO_TRADUCCION[clave_vieja]
                        propiedades_limpias[clave_nueva] = valor
                    else:
                        propiedades_limpias[clave_vieja.lower()] = valor

                feature['properties'] = propiedades_limpias

            nueva_capa = CapaGeografica(
                nombre_capa=request.data.get('nombre_capa'),
                estado=request.data.get('estado'),
                municipio=request.data.get('municipio'),
                categoria=request.data.get('categoria'),
                tipo_geometria=request.data.get('tipo_geometria'),
                archivo_original=archivo_subido, 
                datos_normalizados=datos_geojson, 
                subido_por=request.user if request.user.is_authenticated else None
            )
            nueva_capa.save()

            return Response({
                "mensaje": "Capa procesada y normalizada exitosamente."
            }, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Hubo un error al procesar el archivo: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        if not pk:
            return Response({"error": "Debes proporcionar el ID de la capa a eliminar."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            capa = CapaGeografica.objects.get(pk=pk)
            nombre = capa.nombre_capa

            if capa.archivo_original:
                try:
                    capa.archivo_original.delete(save=False)
                except Exception:
                    pass  
            capa.delete()
            return Response({"mensaje": f"Capa '{nombre}' eliminada exitosamente."}, status=status.HTTP_200_OK)
        except CapaGeografica.DoesNotExist:
            return Response({"error": "Capa no encontrada."}, status=status.HTTP_404_NOT_FOUND)