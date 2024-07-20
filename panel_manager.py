import os
import zipfile
import rarfile
from utils import parse_gui_file, save_gui_file, ensure_directory_exists
from PIL import Image
from logger import logger
import subprocess
class PanelManager:
    # def __init__(self, input_file):
    #     self.input_file = input_file
    #     self.extract_dir = 'extracted_comic'
    #     ensure_directory_exists(self.extract_dir)
    #     self.archive = self.open_archive(input_file)
    #     self.panel_corrections = self.load_gui_file()
    #     logger.info(f"PanelManager initialized for {input_file}")

    def open_archive(self, file_path):
        logger.info(f"Attempting to open archive: {file_path}")
        if file_path.lower().endswith(('.cbr', '.rar')):
            logger.debug("Opening RAR archive")
            return rarfile.RarFile(file_path)
        elif file_path.lower().endswith(('.cbz', '.zip')):
            logger.debug("Opening ZIP archive")
            return zipfile.ZipFile(file_path)
        else:
            logger.error(f"Unsupported file format: {file_path}")
            raise ValueError("Formato de archivo no soportado")

    def get_image_files(self):
        files = sorted([f for f in self.archive.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png'))])
        logger.debug(f"Found {len(files)} image files in archive")
        return files

    # def extract_page(self, page_index):
    #     image_files = self.get_image_files()
    #     extracted_path = os.path.join(self.extract_dir, image_files[page_index])
    #     try:
    #         self.archive.extract(image_files[page_index], path=self.extract_dir)
    #         logger.info(f"Extracted page {page_index} to {extracted_path}")
    #         return extracted_path
    #     except rarfile.BadRarFile as e:
    #         logger.error(f"Error extracting page {page_index}: {e}")
    #         return None

    def load_gui_file(self):
        gui_path = self.input_file + ".gui"
        if os.path.exists(gui_path):
            logger.info(f"Loading GUI file: {gui_path}")
            return parse_gui_file(gui_path)
        else:
            logger.info("No GUI file found, starting with empty corrections")
            return {}

    # def get_panels(self, page):
    #     panels = self.panel_corrections.get(page, [])
    #     logger.debug(f"Got {len(panels)} panels for page {page}")
    #     return panels

    # def delete_panel(self, page, panel_index):
    #     if page in self.panel_corrections and panel_index < len(self.panel_corrections[page]):
    #         del self.panel_corrections[page][panel_index]
    #         if not self.panel_corrections[page]:
    #             del self.panel_corrections[page]
    #         logger.info(f"Deleted panel {panel_index} from page {page}")
    #     else:
    #         logger.warning(f"Attempted to delete non-existent panel {panel_index} from page {page}")

    # def save_gui_file(self):
    #     gui_path = self.input_file + ".gui"
    #     save_gui_file(gui_path, self.panel_corrections)
    #     logger.info(f"Saved GUI file: {gui_path}")

    # def get_num_pages(self):
    #     num_pages = len(self.get_image_files())
    #     logger.debug(f"Comic has {num_pages} pages")
    #     return num_pages

    # def get_page_path(self, page_index):
    #     path = self.extract_page(page_index)
    #     if path is None:
    #         logger.error(f"Could not extract page {page_index}")
    #         raise ValueError(f"No se pudo extraer la página {page_index}")
    #     return path
    
    
    # def get_page_path(self, page_index):
    #     image_files = self.get_image_files()
    #     if 0 <= page_index < len(image_files):
    #         path = self.extract_page(page_index)
    #         if path is None or not os.path.exists(path):
    #             raise ValueError(f"No se pudo extraer la página {page_index}")
    #         return path
    #     else:
    #         raise ValueError(f"Índice de página inválido: {page_index}")    
            
            






    def get_panels(self, page):
        return self.panel_corrections.get(page, [])

    def delete_panel(self, page, panel_index):
        del self.panel_corrections[page][panel_index]
        if not self.panel_corrections[page]:
            del self.panel_corrections[page]

    # def save_gui_file(self):
    #     save_gui_file(self.input_file + ".gui", self.panel_corrections)

    def get_num_pages(self):
        return len(self.valid_files)

    def get_page_path(self, page_index):
        if page_index < len(self.valid_files):
            return os.path.join(self.extract_dir, self.valid_files[page_index])
        else:
            raise ValueError(f"No se pudo extraer la página {page_index}")

    def extract_page(self, page_index):
        page_path = self.get_page_path(page_index)
        return page_path

    # def set_panels(self, page, panels):
    #     self.panel_corrections[page] = panels
        
    def __init__(self, input_file):
        self.input_file = input_file
        self.extract_dir = 'extracted_comic'
        ensure_directory_exists(self.extract_dir)
        self.panel_corrections = self.load_gui_file()
        self.valid_files = []
        self.archive = self.open_archive(input_file)
        self.valid_files = self.extract_all_files()        
        
    def extract_all_files(self):
        valid_files = []
        image_files = self.get_image_files()
        for file in image_files:
            try:
                self.archive.extract(file, path=self.extract_dir)
                valid_files.append(file)
            except (zipfile.BadZipFile, KeyError) as e:
                print(f"Error al extraer el archivo {file}: {e}")
        return valid_files            
    
    
    
    
    def set_panels(self, page, panels):
        """
        Establece los paneles para una página específica.
        
        :param page: Número de página (índice empezando en 0)
        :param panels: Lista de paneles (cada panel es una tupla de 4 elementos: x1, y1, x2, y2)
        """
        logger.info(f"Setting panels for page {page + 1}")
        self.panel_corrections[page] = panels
        self.save_gui_file()
        logger.info(f"Set {len(panels)} panels for page {page + 1}") 
    
    
    def save_gui_file(self):
        gui_path = self.input_file + ".gui"
        save_gui_file(gui_path, self.panel_corrections)
        logger.info(f"Saved GUI file: {gui_path}")    
        
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    
    