import json
import os
import django
import sys
import random

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backurban.settings')
django.setup()

from yucatan_capas.models import modelo_predio_yucatan_centro
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon

def safe_float(value, default=0.0):
    try:
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default

def importar():
    ruta = 'ahorasi.geojson' 
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
        
        try:
            total_const = prop.get('Join_Count', 0) or 0
            area_predio = safe_float(prop.get('area_pred'))

            pisos_str = str(prop.get('pisos') or '0')
            mats_str = str(prop.get('material') or 'N/A')
            area_c_str = str(prop.get('area_cons') or '0')
            z_c_str = str(prop.get('z_construccion') or '0')

            lista_pisos = [p.strip() for p in pisos_str.split(',') if p.strip()]
            lista_mats = [m.strip() for m in mats_str.split(',') if m.strip()]
            lista_area = [a.strip() for a in area_c_str.split(',') if a.strip()]
            lista_z = [z.strip() for z in z_c_str.split(',') if z.strip()]

            estructuras = []
            suma_pisos = 0
            
            for p, m, a, z in zip(lista_pisos, lista_mats, lista_area, lista_z):
                try:
                    val_piso = int(float(p))
                except:
                    val_piso = 0
                
                estructuras.append({
                    "p": val_piso, 
                    "m": m, 
                    "a": safe_float(a), 
                    "z": safe_float(z)
                })
                suma_pisos += val_piso

            equipos = {
                'templo':       prop.get('Join_Count_12_13', 0) or 0,
                'cementerio':   prop.get('Join_Count_12_13_14_15_16_17_18_19_20_21', 0) or 0,
                'ruina':        prop.get('Join_Count_12_13_14_15', 0) or 0,
                'plaza':        prop.get('Join_Count_12_13_14_15_16_17_18', 0) or 0,
                'mercado':      prop.get('Join_Count_12_13_14_15_16_17', 0) or 0,
                'invernadero':  prop.get('Join_Count_12_13_14_15_16', 0) or 0,
                'gasolineria':  prop.get('Join_Count_12_13_14_15_16_17_18_19', 0) or 0,
                'escuela':      prop.get('Join_Count_12_13_14_15_16_17_18_19_20', 0) or 0,
                'subestacion':  prop.get('Join_Count_12_13_14_15_16_17_18_19_20_21_22', 0) or 0,
                'aeropuerto':   prop.get('Join_Count_12_13_14', 0) or 0,
            }

            suma_actual = sum(equipos.values())
            remanente = total_const - suma_actual

            if remanente > 0:
                if area_predio < 250:
                    pool = ['templo', 'mercado', 'plaza', 'escuela']
                else:
                    pool = ['templo', 'mercado', 'plaza', 'escuela', 'ruina', 'invernadero']
                
                random.shuffle(pool)
                idx = 0
                while remanente > 0:
                    cat = pool[idx % len(pool)]
                    equipos[cat] += 1
                    remanente -= 1
                    idx += 1

            g = GEOSGeometry(json.dumps(feature['geometry']))
            g.srid = 4326
            if g.geom_type == 'Polygon': g = MultiPolygon(g)

            modelo_predio_yucatan_centro.objects.create(
                **equipos,
                paneles = prop.get('Join_Count_12', 0) or 0,
                total_construcciones = total_const,
                total_pisos_acumulados = suma_pisos,
                datos_estructurales = estructuras,
                area_total = area_predio,
                longitud_total = safe_float(prop.get('leng_pred')),
                z_valor = safe_float(prop.get('z_pred') or prop.get('Z')),
                codigo = str(prop.get('codigo') or 'S/C'),
                categoria = str(prop.get('categoria') or 'S/CAT'),
                geom = g
            )

            if i % 100 == 0:
                print(f"Progresando: {i}/{total}...")

        except Exception as e:
            print(f"Error en predio {i}: {e}")

    print("--- IMPORTACIÓN FINALIZADA ---")

if __name__ == "__main__":
    importar()