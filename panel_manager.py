import os
import zipfile
import rarfile
from utils import parse_gui_file, save_gui_file, ensure_directory_exists
from PIL import Image

class PanelManager:
    def __init__(self, input_file):
        self.input_file = input_file
        self.extract_dir = 'extracted_comic'
        ensure_directory_exists(self.extract_dir)
        self.archive = self.open_archive(input_file)
        self.panel_corrections = self.load_gui_file()

    def open_archive(self, file_path):
        print(f"Intentando abrir el archivo: {file_path}")
        if file_path.lower().endswith(('.cbr', '.rar')):
            return rarfile.RarFile(file_path)
        elif file_path.lower().endswith(('.cbz', '.zip')):
            return zipfile.ZipFile(file_path)
        else:
            raise ValueError("Formato de archivo no soportado")

    def get_image_files(self):
        return sorted([f for f in self.archive.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))])

    def extract_page(self, page_index):
        image_files = self.get_image_files()
        extracted_path = os.path.join(self.extract_dir, image_files[page_index])
        try:
            self.archive.extract(image_files[page_index], path=self.extract_dir)
        except rarfile.BadRarFile as e:
            print(f"Error al extraer la página: {e}")
            return None
        return extracted_path

    def load_gui_file(self):
        gui_path = self.input_file + ".gui"
        if os.path.exists(gui_path):
            return parse_gui_file(gui_path)
        else:
            return {}

    def get_panels(self, page):
        return self.panel_corrections.get(page, [])

    def delete_panel(self, page, panel_index):
        del self.panel_corrections[page][panel_index]
        if not self.panel_corrections[page]:
            del self.panel_corrections[page]

    def save_gui_file(self):
        save_gui_file(self.input_file + ".gui", self.panel_corrections)

    def get_num_pages(self):
        return len(self.get_image_files())

    def get_page_path(self, page_index):
        path = self.extract_page(page_index)
        if path is None:
            raise ValueError(f"No se pudo extraer la página {page_index}")
        return path
