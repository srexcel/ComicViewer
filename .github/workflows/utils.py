import os

def ensure_directory_exists(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)

def parse_gui_file(gui_path):
    panels = {}
    with open(gui_path, 'r') as f:
        lines = f.readlines()
        for line in lines:
            if line.strip():
                parts = line.strip().split(':')
                page = int(parts[0].replace('page', ''))
                coords = parts[1].split(';')
                panels[page] = [(int(float(x.split('_')[0].strip())), int(float(x.split('_')[1].strip())), 
                                 int(float(y.split('_')[0].strip())), int(float(y.split('_')[1].strip()))) for x, y in zip(coords[0::2], coords[1::2])]
    return panels

def save_gui_file(gui_path, panels):
    with open(gui_path, 'w') as f:
        for page, coords in panels.items():
            coord_str = ';'.join([f"{x1}_{y1};{x2}_{y2}" for x1, y1, x2, y2 in coords])
            f.write(f"page{page}: {coord_str}\n")
