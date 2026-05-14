import json
import os

def analizar_geojson(nombre_archivo):
    if not os.path.exists(nombre_archivo):
        print(f"Error: No se encuentra el archivo {nombre_archivo}")
        return

    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        data = json.load(f)

    features = data.get('features', [])
    
    # Diccionario para agrupar hallazgos
    # Estructura: { 'MURO': {'conteo': 10, 'campos': set()}, 'CERCAS': ... }
    resumen = {}

    print(f"Analizando {len(features)} elementos...\n")

    for feature in features:
        prop = feature.get('properties', {})
        tipo_objeto = prop.get('OBJETO', 'SIN_NOMBRE')

        if tipo_objeto not in resumen:
            resumen[tipo_objeto] = {
                'conteo': 0,
                'ejemplo_campos': set()
            }
        
        # Sumar al contador
        resumen[tipo_objeto]['conteo'] += 1
        
        # Registrar qué campos trae este tipo de objeto
        for llave in prop.keys():
            resumen[tipo_objeto]['ejemplo_campos'].add(llave)

    # Imprimir resultados en consola de forma organizada
    print(f"{'TIPO DE OBJETO':<20} | {'CANTIDAD':<10} | {'CAMPOS DISPONIBLES'}")
    print("-" * 70)
    
    for objeto, info in resumen.items():
        campos = ", ".join(sorted(info['ejemplo_campos']))
        print(f"{objeto:<20} | {info['conteo']:<10} | {campos}")

if __name__ == "__main__":
    # Cambia esto por el nombre de tu archivo de líneas o puntos
    analizar_geojson('otros.geojson')