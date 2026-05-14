import json
import os
import django
import sys

# Configuración de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backurban.settings')
django.setup()

from izucar_matamoros_capas.models import modelo_simbolos
from django.contrib.gis.geos import GEOSGeometry

def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def importar_puntos():
    ruta = 'simbolos.geojson' 
    
    if not os.path.exists(ruta):
        print(f"No se encontró el archivo {ruta}")
        return

    with open(ruta, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    features = data.get('features', [])
    total = len(features)
    print(f"Iniciando importación de {total} puntos...")

    for i, feature in enumerate(features):
        prop = feature['properties']
        geom_data = feature['geometry']
        
        try:
            g = GEOSGeometry(json.dumps(geom_data))
            g.srid = 4326

            modelo_simbolos.objects.create(
                objeto = str(prop.get('OBJETO', 'PUNTO')),
                geom = g
            )

            if i % 500 == 0:
                print(f"Procesando puntos: {i}/{total}...")

        except Exception as e:
            print(f"Error en punto {i}: {e}")

    print("--- ! IMPORTACIÓN DE PUNTOS FINALIZADA ! ---")

if __name__ == "__main__":
    importar_puntos()