import json
import os 
import django
import sys

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backurban.settings')
django.setup()

from izucar_matamoros_capas.models import modelo_vector
from django.contrib.gis.geos import GEOSGeometry, MultiLineString

def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def importar():
    ruta = 'vectores.geojson'
    
    if not os.path.exists(ruta):
        print(f"No se encontró el archivo {ruta}")
        return
    
    with open(ruta, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    total = len(features)
    print(f"Iniciando importación: {total} registros...")

    for i, feature in enumerate(features):
        prop = feature['properties']
        geom_data = feature['geometry']

        try:
            g = GEOSGeometry(json.dumps(geom_data))
            g.srid = 4326

            if g.geom_type == 'LineString':
                g = MultiLineString(g)


            modelo_vector.objects.create(
                objeto = str(prop.get('OBJETO') or prop.get('objeto') or 'VECTOR'),
                longitud = safe_float(prop.get('Shape_Length') or prop.get('longitud')),
                geom = g
            )

            if i % 100 == 0:
                print(f"Progresando: {i}/{total}...")

        except Exception as e:
            oid = prop.get('OBJECTID', i)
            print(f"Error en registro {i} (ID: {oid}): {e}")

    print("\n--- ! IMPORTACIÓN FINALIZADA CON ÉXITO ! ---")

if __name__ == "__main__":
    importar()