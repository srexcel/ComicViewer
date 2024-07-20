import os
import json
def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_gui_file(gui_path):
    panels = {}
    if not os.path.exists(gui_path):
        return panels
    
    with open(gui_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            line = line.strip()
            if line:
                try:
                    parts = line.split(':')
                    if len(parts) != 2:
                        continue
                    page = int(parts[0].replace('page', '').strip())
                    coords = parts[1].split(';')
                    panels[page] = []
                    for i in range(0, len(coords), 2):
                        if i+1 < len(coords):
                            x, y = coords[i].strip(), coords[i+1].strip()
                            x1, y1 = map(lambda v: int(float(v)), x.split('_'))
                            x2, y2 = map(lambda v: int(float(v)), y.split('_'))
                            panels[page].append((x1, y1, x2, y2))
                except ValueError:
                    # Si hay un error al convertir los valores, simplemente
                    # saltamos esta línea y continuamos con la siguiente
                    continue
    return panels

def save_gui_file(gui_path, panels):
    with open(gui_path, 'w') as f:
        for page, coords in panels.items():
            coord_str = ';'.join([f"{x1}_{y1};{x2}_{y2}" for x1, y1, x2, y2 in coords])
            f.write(f"page{page}: {coord_str}\n")
            
# def load_api_keys():
#     keys_file = 'KEYS.json'
#     if os.path.exists(keys_file):
#         with open(keys_file, 'r') as f:
#             return json.load(f)
#     return {}

# def save_api_keys(keys):
#     keys_file = 'KEYS.json'
#     with open(keys_file, 'w') as f:
#         json.dump(keys, f, indent=4)            
            
# En utils.py



def load_api_keys():
    keys_file = 'KEYS.json'
    if not os.path.exists(keys_file):
        # Si el archivo no existe, lo creamos con un diccionario vacío
        save_api_keys({})
        print("Archivo KEYS.json creado.")
        return {}
    
    with open(keys_file, 'r') as f:
        try:
            keys = json.load(f)
            if not keys:
                print("El archivo KEYS.json está vacío.")
            return keys
        except json.JSONDecodeError:
            print("El archivo KEYS.json está corrupto o vacío. Se creará uno nuevo.")
            save_api_keys({})
            return {}

def save_api_keys(keys):
    keys_file = 'KEYS.json'
    with open(keys_file, 'w') as f:
        json.dump(keys, f, indent=4)

def validate_api_key(service, api_key):
    # Aquí implementaremos la lógica para validar las claves API
    # Esta es una implementación de ejemplo, deberás adaptarla según cada servicio
    if service == 'deepl':
        # Validación para DeepL
        import deepl
        try:
            translator = deepl.Translator(api_key)
            translator.get_usage()
            return True
        except:
            return False
    elif service == 'chatgpt':
        # Validación para ChatGPT
        import openai
        try:
            openai.api_key = api_key
            openai.Model.list()
            return True
        except:
            return False
    else:
        # Para otros servicios que no requieren validación (como Google Translate)
        return True