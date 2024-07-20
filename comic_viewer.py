import json
import os
import logging
import platform
import sys
import random
import urllib.parse
import webbrowser
import pyperclip
from tkinter import *
from tkinter import ttk, messagebox, simpledialog, filedialog
from PIL import Image, ImageTk
from panel_manager import PanelManager
from panel_editor import PanelEditor
from panel_order_editor import PanelOrderEditor
from panel_recalculation import recalcular_paneles
from utils import ensure_directory_exists
from state_manager import save_state, load_state
from translation_manager import TranslationManager
from translation_configurator import TranslationConfiguratorApp
from translation_editor import TranslationEditor
from tkinter import TclError, SEL_FIRST, SEL_LAST


def setup_logger():
    logging.basicConfig(filename='comic_viewer.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('ComicViewer')
    logger.info("System Information:")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Processor: {platform.processor()}")
    logger.info(f"Machine: {platform.machine()}")
    return logger

logger = setup_logger()

def log_function(func):
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering function: {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Exiting function: {func.__name__}")
        return result
    return wrapper

class ComicViewer:

        
    @log_function
    def __init__(self, root):
        self.translation_text = Text(root)
        self.comments_text = Text(root)
        self.root = root
        self.root.title("Comic Viewer")
        self.panel_mode = False
        self.create_ui()
        self.current_page = 0
        self.current_panel = 0
        self.panels_to_show = 1
        self.viewing_panels = False
        self.extract_dir = 'extracted_comic'
        ensure_directory_exists(self.extract_dir)
        self.translation_mode = False
        self.translations = {}
        
        self.panel_manager = None
    
        self.panel_images = []
        self.current_image = None
        self.canvas.bind('<Configure>', self.on_resize)
        
        self.translation_manager = TranslationManager(self, self.panel_manager)
        self.translation_window = None
        self.text_size = 12
        logger.info("ComicViewer initialized")
        self.check_last_file()
        self.translate_button = Button(self.button_frame, text="Traducir", command=self.start_translation, state='disabled')
        self.translate_button.pack(fill=X)
        self.translation_config = {
            "google": None,
            "deepl": None,
            "chatgpt": None
        }
        self.translation_widgets = []
        self.update_status()
        
        # Asegúrate de definir todas las funciones referenciadas por los botones
        self.increase_text_size = self.dummy_function
        self.decrease_text_size = self.dummy_function
        self.advanced_web_search = self.dummy_function
        self.create_temp_ocr = self.dummy_function
        self.previous_panel = self.dummy_function
        self.next_panel = self.dummy_function
        self.go_to_panel = self.dummy_function
        
    def search_web(self):
        try:
            selection = self.translation_text.get(SEL_FIRST, SEL_LAST)
        except TclError:
            selection = None
        if selection:
            reverso_url = f"https://www.reverso.net/Text%C3%BCbersetzung#sl=ger&tl=spa&text={urllib.parse.quote(selection)}"
            deepl_url = f"https://www.deepl.com/translator#de/en/{urllib.parse.quote(selection)}"
            wordreference_url = f"https://www.wordreference.com/deen/{urllib.parse.quote(selection)}"
            
            webbrowser.open(reverso_url)
            webbrowser.open(deepl_url)
            webbrowser.open(wordreference_url)
            
            prompt = (
                "Traduce la frase que te pongo de acuerdo a las siguientes pautas:\n\n"
                "Objetivo de Traducción y Explicación:\n\n"
                "El objetivo es comprender las frases compuestas y las particularidades del idioma alemán con un enfoque didáctico para hispanohablantes.\n"
                "Si la frase proviene de un cómic, analiza los diálogos para entender la gramática alemana.\n"
                "Formato Preferido:\n\n"
                "Incluye la traducción completa de la frase.\n"
                "Realiza un desglose detallado de cada oración.\n"
                "Analiza las palabras compuestas, explicando sus componentes y significados.\n"
                "Proporciona una reflexión general sobre el contenido analizado.\n"
                "Asegúrate de analizar al menos tres palabras compuestas por párrafo.\n"
                "Sección de Palabras Polisémicas:\n\n"
                "Incluye una sección dedicada a las palabras polisémicas presentes en el texto.\n"
                f"Frase: {selection}"
            )
            
            pyperclip.copy(prompt)
            
            messagebox.showinfo("Información", "Se han abierto las páginas web con el prompt incluido y se ha copiado al portapapeles.")
        else:
            messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")

    def load_translation_and_comments(self, translation, comments):
        self.translation_text.delete('1.0', END)
        self.translation_text.insert('1.0', translation)
        self.comments_text.delete('1.0', END)
        self.comments_text.insert('1.0', comments)
        
    @log_function
    def dummy_function(self):
        # Esta es una función de ejemplo que se puede reemplazar con la funcionalidad real
        print("Función de prueba llamada.")
        

    @log_function
    def create_ui(self):
        
        self.frame = Frame(self.root)
        self.frame.pack(fill=BOTH, expand=1)
    
        self.canvas_frame = Frame(self.frame)
        self.canvas_frame.pack(side=LEFT, fill=BOTH, expand=1)
    
        self.canvas = Canvas(self.canvas_frame, bg='white')
        self.canvas.pack(side=LEFT, fill=BOTH, expand=1)
    
        self.scrollbar = Scrollbar(self.canvas_frame, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side=RIGHT, fill=Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox('all')))
    
        self.button_frame = Frame(self.frame)
        self.button_frame.pack(side=RIGHT, fill=Y)
    
        self.load_button = Button(self.button_frame, text="Cargar Cómic", command=self.load_comic)
        self.load_button.pack(fill=X)
        self.prev_page_button = Button(self.button_frame, text="Página Anterior", command=self.prev_page)
        self.prev_page_button.pack(fill=X)
        self.next_page_button = Button(self.button_frame, text="Siguiente Página", command=self.next_page)
        self.next_page_button.pack(fill=X)
        self.prev_panel_button = Button(self.button_frame, text="Panel Anterior", command=self.prev_panel)
        self.prev_panel_button.pack(fill=X)
        self.next_panel_button = Button(self.button_frame, text="Siguiente Panel", command=self.next_panel)
        self.next_panel_button.pack(fill=X)
        self.toggle_button = Button(self.button_frame, text="Ver Paneles", command=self.toggle_panels)
        self.toggle_button.pack(fill=X)
        self.recalc_button = Button(self.button_frame, text="Recalcular Paneles", command=self.recalculate_panels)
        self.recalc_button.pack(fill=X)
        self.reorder_button = Button(self.button_frame, text="Reordenar Paneles", command=self.reorder_panels)
        self.reorder_button.pack(fill=X)
        self.delete_panel_button = Button(self.button_frame, text="Borrar Panel", command=self.delete_current_panel)
        self.delete_panel_button.pack(fill=X)
        self.add_panel_button = Button(self.button_frame, text="Agregar/Modificar Panel", command=self.add_modify_panel)
        self.add_panel_button.pack(fill=X)
        self.fit_image_button = Button(self.button_frame, text="Ajustar Imagen", command=self.fit_image)
        self.fit_image_button.pack(fill=X)
        self.info_label = Label(self.button_frame, text="", anchor='w')
        self.info_label.pack(fill=X)
    
        self.translation_config_button = Button(self.button_frame, text="Configuración de traducción", command=self.open_translation_config)
        self.translation_config_button.pack(fill=X)
        self.view_translation_button = Button(self.button_frame, text="Ver traducción", command=self.toggle_translation_view)
        self.view_translation_button.pack(fill=X)
    
        self.status_label = Label(self.button_frame, text="Modo: Página", anchor='w')
        self.status_label.pack(fill=X)
    
        logger.info("UI created")

        

#Inserta codigo a partir de aq








    def check_last_file(self):
        state = load_state()
        if state:
            message_window = Toplevel(self.root)
            message_window.title("Continuar lectura")
            message_window.geometry(f"+{self.root.winfo_x()}+{self.root.winfo_y()}")
            message_window.attributes('-topmost', True)
            
            message = "¿Deseas continuar la lectura anterior?\n\n(Este programa requiere WinRar instalado)"
            Label(message_window, text=message, padx=20, pady=10).pack()
            
            def handle_response(response):
                message_window.destroy()
                if response:
                    self.load_comic(state.get('last_file'), 
                                    state.get('current_page', 0), 
                                    state.get('current_panel', 0), 
                                    state.get('viewing_panels', False))
            
            Button(message_window, text="Sí", command=lambda: handle_response(True)).pack(side=LEFT, padx=10, pady=10)
            Button(message_window, text="No", command=lambda: handle_response(False)).pack(side=RIGHT, padx=10, pady=10)
            
            self.root.wait_window(message_window)
        else:
            logger.info("No previous state found")


    def open_translation_window(self):
        if self.translation_window is None or not self.translation_window.winfo_exists():
            self.translation_window = Toplevel(self.root)
            self.translation_window.title("Texto de panel")
            self.translation_window.geometry("600x800")
    
            main_frame = Frame(self.translation_window)
            main_frame.pack(fill=BOTH, expand=1)
    
            self.translation_text = Text(main_frame, wrap=WORD, font=("Arial", self.text_size))
            self.translation_text.pack(fill=BOTH, expand=1)
    
            # Añadir caja de comentarios redimensionable
            comments_frame = Frame(main_frame)
            comments_frame.pack(fill=X, pady=5)
            
            comments_label = Label(comments_frame, text="Comentarios:", anchor='w')
            comments_label.pack(fill=X)
            
            self.comments_text = Text(comments_frame, wrap=WORD, height=3)
            self.comments_text.pack(fill=X, expand=1)
            
            # Hacer que la caja de comentarios sea redimensionable
            comments_sizer = ttk.Sizegrip(comments_frame)
            comments_sizer.pack(side=RIGHT, anchor='se')
    
            button_frame = Frame(self.translation_window)
            button_frame.pack(fill=X, pady=5)
    
            close_button = Button(button_frame, text="Cerrar", command=self.translation_window.destroy)
            close_button.pack(side=LEFT, padx=5)
    
            save_button = Button(button_frame, text="Guardar cambios", command=self.save_translation_changes)
            save_button.pack(side=LEFT, padx=5)
    
            comments_button = Button(button_frame, text="Comentarios", command=self.open_comments_window)
            comments_button.pack(side=LEFT, padx=5)
    
            web_search_button = Button(button_frame, text="Búsqueda web", command=self.search_web)
            web_search_button.pack(side=LEFT, padx=5)
    
            increase_text_size_button = Button(button_frame, text="Aumentar tamaño de texto", command=self.increase_text_size)
            increase_text_size_button.pack(side=LEFT, padx=5)
    
            decrease_text_size_button = Button(button_frame, text="Disminuir tamaño de texto", command=self.decrease_text_size)
            decrease_text_size_button.pack(side=LEFT, padx=5)
    
            self.load_translations_to_text()
        else:
            self.translation_window.lift()



    def save_translation_changes(self):
        content = self.translation_text.get(1.0, END).strip()
        comments = self.comments_text.get(1.0, END).strip()
        if content:
            try:
                translations = self.parse_translation_content(content)
                filename = f"{os.path.splitext(self.panel_manager.input_file)[0]}_trans.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(translations, f, ensure_ascii=False, indent=4)
                
                # Guardar comentarios
                comments_filename = f"{os.path.splitext(self.panel_manager.input_file)[0]}_comments.json"
                if os.path.exists(comments_filename):
                    with open(comments_filename, 'r', encoding='utf-8') as f:
                        all_comments = json.load(f)
                else:
                    all_comments = {}
                all_comments[str(self.current_page)] = comments
                with open(comments_filename, 'w', encoding='utf-8') as f:
                    json.dump(all_comments, f, ensure_ascii=False, indent=4)
                
                messagebox.showinfo("Guardado", "Cambios y comentarios guardados correctamente.")
            except Exception as e:
                logger.error(f"Error saving translations: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Error al guardar las traducciones: {str(e)}")
        else:
            messagebox.showwarning("Advertencia", "No hay contenido para guardar.")





    # def search_web(self):
    #     try:
    #         selection = self.translation_text.get(SEL_FIRST, SEL_LAST)
    #     except TclError:
    #         selection = None
    #     if selection:
    #         webbrowser.open("https://www.reverso.net/text_translation.aspx?lang=de")
    #         webbrowser.open(f"https://www.deepl.com/translator#de/en/{urllib.parse.quote(selection)}")
    #         webbrowser.open(f"https://www.wordreference.com/deen/{urllib.parse.quote(selection)}")
            
    #         prompt = (
    #             "Traduce la frase que te pongo de acuerdo a las siguientes pautas:\n\n"
    #             "Objetivo de Traducción y Explicación:\n\n"
    #             "El objetivo es comprender las frases compuestas y las particularidades del idioma alemán con un enfoque didáctico para hispanohablantes.\n"
    #             "Si la frase proviene de un cómic, analiza los diálogos para entender la gramática alemana.\n"
    #             "Formato Preferido:\n\n"
    #             "Incluye la traducción completa de la frase.\n"
    #             "Realiza un desglose detallado de cada oración.\n"
    #             "Analiza las palabras compuestas, explicando sus componentes y significados.\n"
    #             "Proporciona una reflexión general sobre el contenido analizado.\n"
    #             "Asegúrate de analizar al menos tres palabras compuestas por párrafo.\n"
    #             "Sección de Palabras Polisémicas:\n\n"
    #             "Incluye una sección dedicada a las palabras polisémicas presentes en el texto.\n"
    #             f"Frase: {selection}"
    #         )
            
    #         encoded_prompt = urllib.parse.quote(prompt)
    #         # webbrowser.open(f"https://chat.openai.com/?model=text-davinci-002-render-sha&prompt={encoded_prompt}")
    #         # webbrowser.open(f"https://poe.com/ChatGPT?prompt={encoded_prompt}")
            
    #         messagebox.showinfo("Información", "Se han abierto las páginas web con el prompt incluido.")
    #     else:
    #         messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")
    
    # def increase_text_size(self):
    #     current_size = int(self.translation_text['font'].split()[1])
    #     self.translation_text.configure(font=("Arial", current_size + 2))
    
    # def decrease_text_size(self):
    #     current_size = int(self.translation_text['font'].split()[1])
    #     if current_size > 8:
    #         self.translation_text.configure(font=("Arial", current_size - 2))






    @log_function
    def toggle_translation_view(self):
        if self.translation_window is None or not self.translation_window.winfo_exists():
            self.open_translation_window()
        else:
            self.translation_window.destroy()
            self.translation_window = None

    @log_function
    def next_item(self):
        if self.viewing_panels:
            self.next_panel()
        else:
            self.next_page()
        self.update_status()

    @log_function
    def prev_item(self):
        if self.viewing_panels:
            self.prev_panel()
        else:
            self.prev_page()
        self.update_status()

    @log_function
    def next_page(self):
        if self.current_page < self.panel_manager.get_num_pages() - 1:
            self.current_page += 1
            self.show_page(self.current_page)
        else:
            messagebox.showinfo("Fin", "Has llegado al final del cómic.")
        self.update_status()

    @log_function
    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)
        else:
            messagebox.showinfo("Inicio", "Estás en la primera página del cómic.")
        self.update_status()

    @log_function
    def next_panel(self):
        if self.current_panel < len(self.panel_images) - 1:
            self.current_panel += 1
            self.display_panel()
        else:
            if self.current_page < self.panel_manager.get_num_pages() - 1:
                self.current_page += 1
                self.current_panel = 0
                self.load_page_and_panels()
            else:
                messagebox.showinfo("Fin", "Has llegado al final del cómic.")
        self.update_status()

    @log_function
    def prev_panel(self):
        if self.current_panel > 0:
            self.current_panel -= 1
            self.display_panel()
        else:
            if self.current_page > 0:
                self.current_page -= 1
                self.current_panel = len(self.panel_manager.get_panels(self.current_page)) - 1
                self.load_page_and_panels()
            else:
                messagebox.showinfo("Inicio", "Estás en la primera página del cómic.")
        self.update_status()

    @log_function
    def load_page_and_panels(self):
        self.show_page(self.current_page)
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        if self.panel_images:
            self.display_panel()
        else:
            self.viewing_panels = False
            self.show_page(self.current_page)


#Revisar la Función display_panel

    @log_function
    def display_panel(self):
        if self.current_image is None:
            logger.error("Cannot display panel: current_image is None")
            messagebox.showerror("Error", "No se pudo cargar la imagen de la página actual")
            return
    
        if not self.panel_images:
            logger.warning("No panels defined for the current page")
            messagebox.showwarning("Sin paneles", "No hay paneles definidos para esta página")
            return
    
        if self.current_panel >= len(self.panel_images):
            self.current_panel = len(self.panel_images) - 1
            logger.warning(f"Current panel index out of range. Adjusted to {self.current_panel}")
    
        logger.debug(f"Displaying panel {self.current_panel + 1} of {len(self.panel_images)}")
    
        panel = self.panel_images[self.current_panel]
        x1, y1, x2, y2 = panel
    
        try:
            img = self.current_image.crop((x1, y1, x2, y2))
    
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
    
            img.thumbnail((canvas_width, canvas_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
    
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.photo, anchor='center')
            self.canvas.config(scrollregion=self.canvas.bbox(ALL))
    
            self.update_info_label()
    
            logger.info(f"Successfully displayed panel {self.current_panel + 1} for page {self.current_page + 1}")
        except Exception as e:
            logger.error(f"Error displaying panel: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo mostrar el panel: {str(e)}")

#Verificación de panel_images en show_panels

    @log_function  
    def show_panels(self):
        if self.current_image is None:
            logger.error("Cannot show panels: current_image is None")
            messagebox.showerror("Error", "No se pudo cargar la imagen de la página actual")
            return
    
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        logger.debug(f"Panel images in show_panels: {self.panel_images}")
        if self.panel_images:
            self.display_panel()
        else:
            logger.warning(f"No panels found for page {self.current_page + 1}")
            messagebox.showwarning("Sin paneles", f"No se encontraron paneles en la página {self.current_page + 1}")
            self.show_page(self.current_page)
        logger.info(f"Showing panels for page {self.current_page + 1}, current panel: {self.current_panel + 1}")




######################
    @log_function
    def load_comic(self, file_path=None, page=0, panel=0, viewing_panels=False):
        if file_path is None:
            file_path = filedialog.askopenfilename(filetypes=[("Comic files", "*.cbz *.cbr")])
        
        if file_path:
            logger.info(f"Attempting to load comic: {file_path}")
            try:
                self.panel_manager = PanelManager(file_path)
                self.current_page = int(page)
                self.current_panel = int(panel)
                self.viewing_panels = bool(viewing_panels)
                logger.info(f"Setting initial state: Page {self.current_page + 1}, Panel {self.current_panel + 1}, Viewing panels: {self.viewing_panels}")
                
                image_path = self.panel_manager.get_page_path(self.current_page)
                self.current_image = Image.open(image_path)
                
                if self.viewing_panels:
                    self.show_panels()
                else:
                    self.show_page(self.current_page)
                
                save_state(file_path, self.current_page, self.current_panel, self.viewing_panels)
                logger.info(f"Successfully loaded comic at page {self.current_page + 1}, panel {self.current_panel + 1}, viewing panels: {self.viewing_panels}")
            except Exception as e:
                logger.error(f"Error loading comic {file_path}: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo cargar el cómic: {str(e)}")
        else:
            logger.warning("No file selected for loading")
        
        self.update_status()
    
    
    @log_function      
    def show_page(self, page_index):
        if self.panel_manager:
            logger.info(f"Showing page {page_index + 1}")
            self.current_page = page_index
            self.viewing_panels = False
            self.panel_images = self.panel_manager.get_panels(page_index)
            logger.debug(f"Panel images in show_page: {self.panel_images}")
            self.update_info_label()
            try:
                image_path = self.panel_manager.get_page_path(page_index)
                self.current_image = Image.open(image_path)
                self.display_image(self.current_image)
                save_state(self.panel_manager.input_file, self.current_page, self.current_panel, self.viewing_panels)
            except Exception as e:
                logger.error(f"Error showing page {page_index + 1}: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"No se pudo mostrar la página {page_index + 1}: {str(e)}")
                
                next_valid_page = self.find_next_valid_page(page_index)
                if next_valid_page is not None and next_valid_page != page_index:
                    self.show_page(next_valid_page)
                else:
                    logger.error("No se pudo encontrar una página válida para mostrar")
                    messagebox.showerror("Error", "No se pudo encontrar una página válida para mostrar")
    
    @log_function
    def display_image(self, image):
        try:
            logger.debug(f"Attempting to display image: {image}")
            if isinstance(image, str):
                image = Image.open(image)
            
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            
            if canvas_width <= 1 or canvas_height <= 1:
                logger.warning(f"Invalid canvas dimensions: {canvas_width}x{canvas_height}. Retrying...")
                self.root.update_idletasks()
                canvas_width = self.canvas.winfo_width()
                canvas_height = self.canvas.winfo_height()
            
            img_ratio = image.width / image.height
            canvas_ratio = canvas_width / canvas_height
    
            if img_ratio > canvas_ratio:
                width = canvas_width
                height = int(width / img_ratio)
            else:
                height = canvas_height
                width = int(height * img_ratio)
    
            img = image.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.delete("all")
            self.canvas.create_image(canvas_width//2, canvas_height//2, image=self.photo, anchor='center')
            self.canvas.config(scrollregion=self.canvas.bbox(ALL))
            logger.info(f"Successfully displayed image of size {width}x{height}")
        except Exception as e:
            logger.error(f"Error displaying image: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudo mostrar la imagen: {str(e)}")
            if self.translation_mode:
                self.show_translations()
#################
###################
#EEEEEEEEEEEEEEEEEE
#hasta aqui


        

    def on_resize(self, event):
        if self.panel_manager:
            if self.viewing_panels:
                self.draw_panels()
            else:
                self.fit_image()
        logger.debug(f"Canvas resized to {event.width}x{event.height}")

    def draw_panels(self):
        self.canvas.delete('panel')
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=2, tags='panel')
            self.canvas.create_text(x2 - 10, y1 + 10, text=str(i + 1), fill='red', anchor='ne', tags='panel')
        logger.debug(f"Drew {len(self.panel_images)} panels on canvas")

    def remove_zero_size_panels(self):
        logger.info("Removing zero-size panels")
        original_count = len(self.panel_images)
        self.panel_images = [(x1, y1, x2, y2) for x1, y1, x2, y2 in self.panel_images if (x2 - x1) > 0 and (y2 - y1) > 0]
        self.panel_manager.panel_corrections[self.current_page] = self.panel_images
        self.panel_manager.save_gui_file()
        removed_count = original_count - len(self.panel_images)
        logger.info(f"Removed {removed_count} zero-size panels")
        messagebox.showinfo("Panels Removed", f"{removed_count} zero-size panels were removed.")
        self.refresh_panels()

    def delete_current_panel(self):
        if self.panel_images:
            logger.info(f"Deleting panel {self.current_panel}")
            del self.panel_images[self.current_panel]
            self.panel_manager.panel_corrections[self.current_page] = self.panel_images
            self.panel_manager.save_gui_file()
            if self.current_panel >= len(self.panel_images):
                self.current_panel = len(self.panel_images) - 1
            if self.panel_images:
                self.display_panel()
            else:
                self.show_page(self.current_page)
            logger.info(f"Panel deleted. New panel count: {len(self.panel_images)}")

    def save_new_order(self, new_order):
        logger.info("Saving new panel order")
        reordered_panels = [self.panel_images[i] for i in new_order]
        self.panel_manager.panel_corrections[self.current_page] = reordered_panels
        self.panel_manager.save_gui_file()
        self.panel_images = reordered_panels
        self.refresh_panels()
        logger.info("New panel order saved and applied")

    
    @log_function      
    def find_next_valid_page(self, current_page):
        total_pages = self.panel_manager.get_num_pages()
        for i in range(current_page + 1, total_pages):
            try:
                self.panel_manager.get_page_path(i)
                return i
            except Exception:
                continue
        for i in range(current_page - 1, -1, -1):
            try:
                self.panel_manager.get_page_path(i)
                return i
            except Exception:
                continue
        return None
    
    @log_function  
    def _recalculate_remaining_pages(self, start_page):
        total_pages = self.panel_manager.get_num_pages()
        for page in range(start_page, total_pages):
            self._recalculate_single_page(page)
        messagebox.showinfo("Recálculo completado", f"Se han recalculado los paneles de las páginas {start_page + 1} a {total_pages}.")
    
    @log_function      
    def _recalculate_specific_pages(self):
        page_input = simpledialog.askstring("Recalcular paneles", 
                                            "Alimente páginas con el formato: 1,3,4-8,10,11-12,15")
        if page_input:
            pages_to_recalculate = self._parse_page_input(page_input)
            for page in pages_to_recalculate:
                self._recalculate_single_page(page - 1)
            messagebox.showinfo("Recálculo completado", f"Se han recalculado los paneles de las siguientes páginas: {page_input}")
        else:
            logger.info("User cancelled specific page recalculation")
    
    @log_function      
    def _recalculate_single_page(self, page):
        logger.info(f"Recalculating panels for page {page + 1}")
        try:
            page_path = self.panel_manager.get_page_path(page)
            new_panels = recalcular_paneles(page_path)
            self.panel_manager.set_panels(page, new_panels)
            self.refresh_panels()
            logger.info(f"Panels recalculated for page {page + 1}. New panel count: {len(new_panels)}")
        except Exception as e:
            logger.error(f"Error recalculating panels for page {page + 1}: {str(e)}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron recalcular los paneles de la página {page + 1}: {str(e)}")
    
    @log_function  
    def recalculate_panels(self):
        logger.info("Starting panel recalculation process")
        
        if messagebox.askyesno("Recalcular paneles", "¿Recalcular panel de la página actual?"):
            self._recalculate_single_page(self.current_page)
        else:
            if messagebox.askyesno("Recalcular paneles", "¿Recalcular los paneles de todas las hojas remanentes?"):
                self._recalculate_remaining_pages(self.current_page)
            else:
                if messagebox.askyesno("Recalcular paneles", "¿Recalcular paneles de páginas específicas?"):
                    self._recalculate_specific_pages()
                else:
                    logger.info("Panel recalculation cancelled by user")
                    return
        
        logger.info("Panel recalculation process completed")
    
    @log_function  
    def increase_panels(self):
        max_panels = len(self.panel_images)
        if (self.panels_to_show < max_panels):
            self.panels_to_show += 1
            self.refresh_panels()
            logger.info(f"Increased panels to show: {self.panels_to_show}")
        else:
            logger.warning(f"Cannot increase panels to show above {max_panels}")
            messagebox.showinfo("Límite alcanzado", f"Ya se están mostrando todos los paneles ({max_panels}).")
    
    @log_function  
    def decrease_panels(self):
        if (self.panels_to_show > 1):
            self.panels_to_show -= 1
            self.refresh_panels()
            logger.info(f"Decreased panels to show: {self.panels_to_show}")
        else:
            logger.warning("Cannot decrease panels to show below 1")
            messagebox.showinfo("Límite alcanzado", "No se puede mostrar menos de 1 panel.")
    
    @log_function  
    def refresh_panels(self):
        if self.viewing_panels:
            self.panel_images = self.panel_manager.get_panels(self.current_page)
            end_panel = min(self.current_panel + self.panels_to_show, len(self.panel_images))
            panels_to_display = self.panel_images[self.current_panel:end_panel]
            self.display_multiple_panels(panels_to_display)
        else:
            self.show_page(self.current_page)
            self.update_info_label()
            self.update_status()
        logger.info(f"Refreshed panels. Current page: {self.current_page + 1}, Panels shown: {self.panels_to_show}")
    
    @log_function      
    def display_multiple_panels(self, panels):
        pass

    

    @log_function    
    def _reorder_remaining_pages_automatically(self, start_page):
        total_pages = self.panel_manager.get_num_pages()
        for page in range(start_page, total_pages):
            self._reorder_single_page_automatically(page)
        messagebox.showinfo("Reordenamiento completado", f"Se han reordenado automáticamente los paneles de las páginas {start_page + 1} a {total_pages}.")
    
    @log_function    
    def _reorder_specific_pages_automatically(self):
        page_input = simpledialog.askstring("Reordenar paneles", 
                                            "Ingrese las páginas a reordenar (ejemplo: 1,3,4-8,10,11-12,15):")
        if page_input:
            pages_to_reorder = self._parse_page_input(page_input)
            for page in pages_to_reorder:
                self._reorder_single_page_automáticamente(page - 1)
            messagebox.showinfo("Reordenamiento completado", f"Se han reordenado automáticamente los paneles de las siguientes páginas: {page_input}")
        else:
            logger.info("User cancelled specific page reordering")
    
    @log_function    
    def _reorder_single_page_automáticamente(self, page):
        logger.info(f"Automatically reordering panels for page {page + 1}")
        panels = self.panel_manager.get_panels(page)
        if panels:
            random.shuffle(panels)
            self._save_new_order(page, panels)
        else:
            logger.info(f"No panels to reorder on page {page + 1}")

    @log_function   
    def add_modify_panel(self):
        if self.panel_manager:
            logger.info("Opening panel editor")
            panel_editor = PanelEditor(self.root, self.panel_manager, self.current_page)
            self.root.wait_window(panel_editor.top)
            self.panel_images = self.panel_manager.get_panels(self.current_page)
            self.draw_panels()
            self.update_info_label()
            logger.info("Panel editor closed, panels updated")
    
    @log_function  
    def reorder_remaining_pages(self):
        num_pages = self.panel_manager.get_num_pages()
        for page in range(self.current_page, num_pages):
            panels = self.panel_manager.get_panels(page)
            if panels:
                panels.sort(key=lambda p: (p[1], p[0]))
                self.panel_manager.set_panels(page, panels)
                logger.info(f"Reordenados paneles en página {page + 1}")
        self.load_image()
        messagebox.showinfo("Reordenar", "Se han reordenado todas las hojas remanentes automáticamente.")
    
    @log_function
    def _reorder_and_save_remaining_pages(self):
        logger.info("Reordering and saving all remaining pages")
        for page in range(self.current_page, self.panel_manager.get_num_pages()):
            self._reorder_single_page(page)
        messagebox.showinfo("Reordenar", "Se han reordenado y guardado todas las hojas remanentes automáticamente.")
    
    @log_function
    def _reorder_single_page(self, page):
        panels = self.panel_manager.get_panels(page)
        if panels:
            order_editor = PanelOrderEditor(self.root, self.panel_manager, page, self._save_new_order)
            self.root.wait_window(order_editor.top)
        else:
            messagebox.showinfo("Sin paneles", f"No hay paneles para reordenar en la página {page + 1}")
    
    @log_function
    def reorder_panels(self):
        logger.info("Starting panel reordering process")
        
        if not self.panel_manager:
            logger.warning("No comic loaded, cannot reorder panels")
            messagebox.showwarning("No hay cómic cargado", "Por favor, cargue un cómic antes de reordenar paneles.")
            return
    
        if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de la página actual?"):
            self._reorder_single_page_with_ui(self.current_page)
        else:
            if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de todas las hojas remanentes?"):
                self._reorder_remaining_pages(self.current_page)
            else:
                if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de páginas específicas?"):
                    self._reorder_specific_pages()
                else:
                    logger.info("Panel reordering cancelled by user")
                    return
        
        logger.info("Panel reordering process completed")
    
    @log_function
    def _reorder_single_page_with_ui(self, page):
        logger.info(f"Reordering single page with UI: {page + 1}")
        order_editor = PanelOrderEditor(self.root, self.panel_manager, page, self._save_new_order, self._reorder_remaining_pages)
        self.root.wait_window(order_editor.top)
    
    @log_function
    def _reorder_remaining_pages(self, start_page):
        logger.info(f"Reordering remaining pages starting from page {start_page + 1}")
        total_pages = self.panel_manager.get_num_pages()
        for page in range(start_page, total_pages):
            panels = self.panel_manager.get_panels(page)
            if panels:
                sorted_panels = sorted(panels, key=lambda p: (p[1], p[0]))
                self._save_new_order(page, sorted_panels)
        
        messagebox.showinfo("Reordenamiento completado", f"Se han reordenado los paneles de las páginas {start_page + 1} a {total_pages}.")
        self.refresh_panels()
    
    @log_function
    def _reorder_specific_pages(self):
        page_input = simpledialog.askstring("Reordenar paneles", 
                                            "Ingrese las páginas a reordenar (ejemplo: 1,3,4-8,10,11-12,15):")
        if page_input:
            pages_to_reorder = self._parse_page_input(page_input)
            for page in pages_to_reorder:
                self._reorder_single_page_with_ui(page - 1)
            messagebox.showinfo("Reordenamiento completado", f"Se han reordenado los paneles de las siguientes páginas: {page_input}")
        else:
            logger.info("User cancelled specific page reordering")
    
    @log_function
    def _parse_page_input(self, input_string):
        pages = set()
        for part in input_string.split(','):
            if '-' in part:
                start, end = map(int, part.split('-'))
                pages.update(range(start, end + 1))
            else:
                pages.add(int(part))
        return sorted(pages)
    
    @log_function
    def _save_new_order(self, page, new_order):
        logger.info(f"Saving new panel order for page {page + 1}")
        self.panel_manager.set_panels(page, new_order)
        self.refresh_panels()
    
    @log_function  
    def toggle_panels(self):
        self.viewing_panels = not self.viewing_panels
        if self.viewing_panels:
            self.show_panels()
            self.translate_button['state'] = 'normal'
        else:
            self.show_page(self.current_page)
            self.translate_button['state'] = 'disabled'
    

    @log_function
    def update_translation_config(self, service, api_key):
        self.translation_config[service] = api_key
        if hasattr(self, 'translation_manager'):
            self.translation_manager.config[service] = {'api_key': api_key}
    
    @log_function
    def start_translation(self):
        if self.viewing_panels and self.current_image:
            panel_image = self.get_current_panel_image()
            # translation_editor = TranslationEditor(self.root, self, panel_image, self.current_page, self.current_panel, self.panel_manager.input_file, self.translation_config)
            translation_editor = TranslationEditor(
                self.root, 
                self.root,  # `self.root` es el master
                self,  # `parent`
                self,  # `comic_viewer`
                self.current_page, 
                panel_image,  # Asegúrate de que `panel_image` es una ruta válida de la imagen
                self.current_panel, 
                self.panel_manager.input_file,  # `input_file`
                self.current_page,  # `page`
                self.current_panel,  # `panel`
                self.panel_manager.input_file,  # `comic_file`
                self.translation_config  # `translation_config`
            )
            self.root.wait_window(translation_editor.top)

    @log_function    
    def get_current_panel_image(self):
        if self.viewing_panels and self.current_image:
            panel = self.panel_images[self.current_panel]
            x1, y1, x2, y2 = panel
            return self.current_image.crop((x1, y1, x2, y2))
        return None
    
    @log_function
    def fit_image(self):
        if self.current_image:
            logger.debug("Fitting image to canvas")
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img_ratio = self.current_image.width / self.current_image.height
            canvas_ratio = canvas_width / canvas_height
    
            if (img_ratio > canvas_ratio):
                width = canvas_width
                height = int(width / img_ratio)
            else:
                height = canvas_height
                width = int(height * img_ratio)
    
            img = self.current_image.copy()
            img.thumbnail((width, height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            
            self.canvas.delete("all")
            
            x = (canvas_width - width) // 2
            y = (canvas_height - height) // 2
            
            self.canvas.create_image(x, y, image=self.photo, anchor='nw')
            self.canvas.config(scrollregion=self.canvas.bbox(ALL))
    
            if self.translation_mode:
                self.show_translations()
    
    @log_function
    def toggle_mode(self):
        self.panel_mode = not self.panel_mode
        self.mode_button.config(relief=SUNKEN if self.panel_mode else RAISED, text="Modo Página" if self.panel_mode else "Modo Panel")
        self.update_status()

    @log_function
    def update_status(self):
        mode_text = "Panel" if self.panel_mode else "Página"
        self.status_label.config(text=f"Modo: {mode_text}")
        self.update_info_label()

    @log_function
    def toggle_panel_mode(self):
        self.panel_mode = not self.panel_mode
        self.panel_mode_button.config(relief=SUNKEN if self.panel_mode else RAISED)
        self.update_status()

    @log_function
    def update_info_label(self):
        if self.panel_manager:
            mode = "Panel" if self.panel_mode else "Página"
            info_text = f"Página: {self.current_page + 1} de {self.panel_manager.get_num_pages()} | Panel: {self.current_panel + 1} de {len(self.panel_images)} | Modo: {mode}"
            self.info_label.config(text=info_text)
            logger.debug(f"Updated info label: {info_text}")
    
    @log_function
    def show_panel_translation(self):
        logger.info("Showing translation for the current panel")
        if self.current_panel in self.translations:
            for translation in self.translations[self.current_panel]:
                x1, y1, x2, y2 = translation['bbox']
                self.add_translation_text(translation)
        else:
            logger.warning("No translation found for the current panel")
    
    @log_function
    def show_page_translation(self):
        logger.info("Showing translation for the entire page")
        for panel_num, translations in self.translations.items():
            if panel_num < len(self.panel_images):
                for translation in translations:
                    x1, y1, x2, y2 = translation['bbox']
                    self.add_translation_text(translation)
    

    
    @log_function
    def parse_translation_content(self, content):
        translations = []
        lines = content.split('\n')
        current_panel = None
        current_translation = {'original': '', 'translations': {'Español': '', 'Inglés': ''}}
        for line in lines:
            if line.startswith("Panel"):
                if current_panel is not None:
                    translations.append({'page': self.current_page, 'panel': current_panel, 'texts': current_translation})
                current_panel = int(line.split()[1]) - 1
                current_translation = {'original': '', 'translations': {'Español': '', 'Inglés': ''}}
            elif line.startswith("Original:"):
                current_translation['original'] = line.replace("Original: ", "").strip()
            elif line.startswith("Traducción 1:"):
                current_translation['translations']['Español'] = line.replace("Traducción 1: ", "").strip()
            elif line.startswith("Traducción 2:"):
                current_translation['translations']['Inglés'] = line.replace("Traducción 2: ", "").strip()
        if current_panel is not None:
            translations.append({'page': self.current_page, 'panel': current_panel, 'texts': current_translation})
        return translations
    

    @log_function
    def add_translation_controls(self):
        control_frame = Frame(self.translation_window)
        control_frame.pack(fill=X)
    
        increase_text_size_button = Button(control_frame, text="Aumentar tamaño de texto", command=self.increase_text_size)
        increase_text_size_button.pack(fill=X)
        decrease_text_size_button = Button(control_frame, text="Disminuir tamaño de texto", command=self.decrease_text_size)
        decrease_text_size_button.pack(fill=X)
    
        search_button = Button(control_frame, text="Buscar en la web", command=self.search_web)
        search_button.pack(fill=X)

    @log_function
    def hide_translations(self):
        self.canvas.delete("translation")
        self.translation_widgets.clear()
        logger.info("Translations hidden")
        
        
        
            
    @log_function
    def load_translations(self):
        filename = f"{os.path.splitext(self.panel_manager.input_file)[0]}_trans.json"
        logger.info(f"Loading translations from {filename}")
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    all_translations = json.load(f)
                    self.translations = {item['panel']: item['texts'] for item in all_translations if item['page'] == self.current_page}
                    logger.info(f"Loaded {len(self.translations)} translations for page {self.current_page}")
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                logger.error(f"Error loading translations: {str(e)}", exc_info=True)
                messagebox.showerror("Error", f"Error loading translations: {str(e)}")
                self.translations = {}
        else:
            self.translations = {}
            logger.info("No translations found for current page")
    

    @log_function
    def open_comments_window(self):
        comments_window = Toplevel(self.translation_window)
        comments_window.title("Comentarios")
        comments_window.geometry("400x300")
    
        comments_text = Text(comments_window, wrap=WORD, font=("Arial", 12), bg='white', fg='black')
        comments_text.pack(expand=1, fill=BOTH)
    
        comments_scrollbar = Scrollbar(comments_window, orient=VERTICAL, command=comments_text.yview)
        comments_scrollbar.pack(side=RIGHT, fill=Y)
        comments_text.configure(yscrollcommand=comments_scrollbar.set)
    
        filename = f"{os.path.splitext(self.panel_manager.input_file)[0]}_comments.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
                comments = all_comments.get(str(self.current_page), "")
                comments_text.insert(END, comments)
        else:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    
        def save_comments():
            with open(filename, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
            all_comments[str(self.current_page)] = comments_text.get(1.0, END).strip()
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(all_comments, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Guardado", "Comentarios guardados correctamente.")
    
        save_button = Button(comments_window, text="Guardar comentarios", command=save_comments)
        save_button.pack(fill=X)
    
        close_button = Button(comments_window, text="Cerrar", command=comments_window.destroy)
        close_button.pack(fill=X)

            
            
            

    def open_translation_config(self):
        if hasattr(self, 'config_window') and self.config_window.winfo_exists():
            self.config_window.lift()
        else:
            self.config_window = Tk.Toplevel(self.root)
            self.config_window.title("Configuración de Traducción")
            TranslationConfiguratorApp(self.config_window, self.translation_manager)
            
            def on_close():
                self.config_window.destroy()
                del self.config_window
            
            self.config_window.protocol("WM_DELETE_WINDOW", on_close)

            
    def load_translations_to_text(self):
        self.translation_text.delete(1.0, END)
        filename = f"{os.path.splitext(self.panel_manager.input_file)[0]}_trans.json"
        logger.info(f"Loading translations from {filename}")
        logger.info(f"Current page: {self.current_page}, Current panel: {self.current_panel}")
        
        if os.path.exists(filename):
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    all_translations = json.load(f)
                    
                found_translation = False
                for translation in all_translations:
                    if translation['page'] == self.current_page and translation['panel'] == self.current_panel:
                        found_translation = True
                        self.translation_text.insert(END, f"Página {self.current_page + 1}\n", "page_label")
                        for i, text in enumerate(translation['texts'], 1):
                            self.translation_text.insert(END, f"Panel {i}\n", "panel_label")
                            self.translation_text.insert(END, f"Original: {text['original']}\n")
                            for lang, trans in text['translations'].items():
                                self.translation_text.insert(END, f"Traducción ({lang}): {trans}\n")
                            self.translation_text.insert(END, "\n")
                        break
                
                if not found_translation:
                    self.translation_text.insert(END, f"No hay traducciones disponibles para la página {self.current_page + 1}, panel {self.current_panel + 1}.")
            except Exception as e:
                logger.error(f"Error loading translations: {str(e)}", exc_info=True)
                self.translation_text.insert(END, f"Error al cargar las traducciones: {str(e)}")
        else:
            self.translation_text.insert(END, "No se encontró el archivo de traducciones.")
        
        # Configurar etiquetas para el formato de texto
        self.translation_text.tag_configure("page_label", foreground="red", font=("Arial", self.text_size, "bold"))
        self.translation_text.tag_configure("panel_label", foreground="red", font=("Arial", self.text_size, "bold"))
            
            

if __name__ == "__main__":
    root = Tk()
    viewer = ComicViewer(root)
    root.geometry("1400x1000")
    logger.info("ComicViewer application started")
    root.mainloop()
