import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, TclError, SEL_FIRST, SEL_LAST, END
from PIL import Image, ImageTk
import pytesseract
import json
import os
import pyperclip
import webbrowser
import urllib.parse
import logging
import platform
import sys
import openai
from googletrans import Translator  # Comentar esta línea ya que googletrans no está disponible

# Configuración del logger para registrar eventos
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

# Decorador para registrar la entrada y salida de funciones
def log_function(func):
    def wrapper(*args, **kwargs):
        logger.debug(f"Entering function: {func.__name__}")
        result = func(*args, **kwargs)
        logger.debug(f"Exiting function: {func.__name__}")
        return result
    return wrapper

class TranslationEditor(tk.Toplevel):
    def __init__(self, root, master, parent, comic_viewer, current_page, panel_image, current_panel, input_file, page, panel, comic_file, translation_config):
        super().__init__(master)  # Inicializar tk.Toplevel correctamente
        self.root = root
        self.master = master
        self.parent = parent
        self.comic_viewer = comic_viewer
        self.current_page = current_page
        self.panel_image = panel_image
        self.current_panel = current_panel
        self.input_file = input_file
        self.page = page
        self.panel = panel
        self.comic_file = comic_file
        self.translation_config = translation_config

        self.title(f"Traducción - Página {page + 1}, Panel {panel + 1}")

        self.text_widgets = {'translations': {}, 'original': None}
        self.translations = {}
        self.temp_text = None  # Inicializar como None para evitar múltiples cajas de texto
        self.comments = self.load_comments()
        self.text_areas = []

        self.create_ui()
        self.load_saved_translations()
        self.detect_text_areas()
        self.load_api_keys()

    @log_function
    def create_ui(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.main_frame = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        self.main_frame.grid(row=0, column=0, sticky="nsew")

        self.image_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.image_frame, weight=1)

        self.canvas = tk.Canvas(self.image_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        logger.debug("Canvas para la imagen creado.")

        self.x_scrollbar = ttk.Scrollbar(self.image_frame, orient="horizontal", command=self.canvas.xview)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        self.y_scrollbar = ttk.Scrollbar(self.image_frame, orient="vertical", command=self.canvas.yview)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(xscrollcommand=self.x_scrollbar.set, yscrollcommand=self.y_scrollbar.set)

        self.text_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.text_frame, weight=1)

        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(5, weight=1)

        self.original_text = tk.Text(self.text_frame, wrap=tk.WORD, height=10)
        self.original_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        logger.debug("Widget de texto original creado.")

        self.translation_text = tk.Text(self.text_frame, wrap=tk.WORD, height=10)
        self.translation_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        logger.debug("Widget de texto para la primera traducción creado.")

        self.translation_text_2 = tk.Text(self.text_frame, wrap=tk.WORD, height=10)
        self.translation_text_2.grid(row=2, column=0, sticky="ew", padx=5, pady=5)
        logger.debug("Widget de texto para la segunda traducción creado.")

        ttk.Label(self.text_frame, text="Texto temporal", font=("Helvetica", 10, "bold")).grid(row=3, column=0, sticky="w")

        self.temp_text = tk.Text(self.text_frame, wrap=tk.WORD, height=10)  # Asegurar que se crea solo una caja de texto temporal
        self.temp_text.grid(row=4, column=0, sticky="ew", padx=5, pady=5)
        logger.debug("Widget de texto temporal creado.")

        ttk.Label(self.text_frame, text="Comentarios:").grid(row=5, column=0, sticky="w")
        self.comments_text = tk.Text(self.text_frame, wrap=tk.WORD)
        self.comments_text.grid(row=6, column=0, sticky="nsew", padx=5, pady=5)
        logger.debug("Widget de texto para los comentarios creado.")

        self.create_buttons()
        self.create_navigation_frame()

        self.photo = ImageTk.PhotoImage(self.panel_image)
        logger.debug(f"Image loaded: {self.photo}")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

        self.canvas.bind("<Button-1>", self.start_rectangle)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_rectangle)
        logger.debug("Interfaz de usuario creada correctamente.")










    @log_function
    def load_saved_translations(self):
        filename = f"{os.path.splitext(self.comic_file)[0]}_trans.json"
        logger.debug(f"Loading saved translations from {filename}")
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_translations = json.load(f)
                for translation in all_translations:
                    if translation['page'] == self.page and translation['panel'] == self.panel:
                        self.saved_translations = translation['texts']
                        logger.debug(f"Saved translations found: {self.saved_translations}")
                        self.populate_text_widgets()
                        return
        self.saved_translations = []
        logger.debug("No saved translations found.")
    
    @log_function
    def populate_text_widgets(self):
        for i, text_data in enumerate(self.saved_translations):
            if i == 0:  # Solo poblar la primera entrada para simplificación
                self.original_text.delete(1.0, tk.END)
                self.original_text.insert(tk.END, text_data['original'])
                logger.debug(f"Original text populated: {text_data['original']}")
    
                self.translation_text.delete(1.0, tk.END)
                self.translation_text.insert(tk.END, text_data['translations'].get('Español', ''))
                logger.debug(f"Translation 1 populated: {text_data['translations'].get('Español', '')}")
    
                self.translation_text_2.delete(1.0, tk.END)
                self.translation_text_2.insert(tk.END, text_data['translations'].get('Inglés', ''))
                logger.debug(f"Translation 2 populated: {text_data['translations'].get('Inglés', '')}")




    @log_function
    def reprocess_ocr(self):
        selected_text = self.get_selected_text()
        if selected_text:
            original_language = self.translation_config.get('languages', {}).get('original', 'desconocido')
            prompt = f"Este texto es el resultado de un OCR de un comic en {original_language}, deduce el OCR correcto y traduce al ing esp ger:\n{selected_text}"
            pyperclip.copy(prompt)
            
            services = ["ChatGPT", "Poe", "Perplexity", "Claude", "Bard"]
            choice = simpledialog.askstring("Seleccionar servicio", 
                                            "Elige un servicio para abrir (o escribe otro):",
                                            initialvalue=services[0])
            
            if choice:
                if choice.lower() == "chatgpt":
                    webbrowser.open("https://chat.openai.com/")
                elif choice.lower() == "poe":
                    webbrowser.open("https://poe.com/")
                elif choice.lower() == "perplexity":
                    webbrowser.open("https://www.perplexity.ai/")
                elif choice.lower() == "bard":
                    webbrowser.open("https://bard.google.com/")
                else:
                    webbrowser.open(f"https://www.google.com/search?q={choice}+AI+chat")
            
            messagebox.showinfo("Información", "Pega el portapapeles en tu servicio favorito")
        else:
            messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")

    @log_function
    def load_api_keys(self):
        try:
            with open('KEYS.json', 'r') as f:
                self.api_keys = json.load(f)
            if 'chatgpt' in self.api_keys:
                openai.api_key = self.api_keys['chatgpt'].get('api_key')
        except FileNotFoundError:
            self.api_keys = {}





    @log_function
    def create_buttons(self):
        self.button_frame = ttk.Frame(self)
        self.button_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=10)
        
        self.process_button = ttk.Button(self.button_frame, text="Procesar", command=self.process_text)
        self.process_button.grid(row=0, column=0, padx=5, pady=5)
        
        self.save_button = ttk.Button(self.button_frame, text="Guardar", command=self.save_text)
        self.save_button.grid(row=0, column=1, padx=5, pady=5)
        
        self.api_var = tk.StringVar()
        self.api_var.set("google")
        
        self.api_menu = ttk.OptionMenu(self.button_frame, self.api_var, "google", "google", "deepl", "chatgpt")
        self.api_menu.grid(row=0, column=2, padx=5, pady=5)
        
        self.translate_button = ttk.Button(self.button_frame, text="Traducir", command=self.translate_text)
        self.translate_button.grid(row=0, column=3, padx=5, pady=5)
        
        self.ocr_button = ttk.Button(self.button_frame, text="OCR", command=self.create_temp_ocr)
        self.ocr_button.grid(row=0, column=4, padx=5, pady=5)
        
        self.previous_panel_button = ttk.Button(self.button_frame, text="Panel Anterior", command=self.previous_panel)
        self.previous_panel_button.grid(row=0, column=5, padx=5, pady=5)
        
        self.next_panel_button = ttk.Button(self.button_frame, text="Siguiente Panel", command=self.next_panel)
        self.next_panel_button.grid(row=0, column=6, padx=5, pady=5)
        
        self.increase_text_size_button = ttk.Button(self.button_frame, text="Aumentar tamaño de texto", command=self.increase_text_size)
        self.increase_text_size_button.grid(row=0, column=7, padx=5, pady=5)
        
        self.decrease_text_size_button = ttk.Button(self.button_frame, text="Disminuir tamaño de texto", command=self.decrease_text_size)
        self.decrease_text_size_button.grid(row=0, column=8, padx=5, pady=5)
        
        self.busqueda_web_traduccion_button = ttk.Button(self.button_frame, text="Búsqueda web", command=self.busqueda_web_traduccion)
        self.busqueda_web_traduccion_button.grid(row=0, column=9, padx=5, pady=5)
        
        self.delete_panel_button = ttk.Button(self.button_frame, text="Borrar panel", command=self.delete_panel)
        self.delete_panel_button.grid(row=0, column=10, padx=5, pady=5)
        
        self.reprocess_ocr_button = ttk.Button(self.button_frame, text="Reprocesar OCR", command=self.reprocess_ocr)
        self.reprocess_ocr_button.grid(row=0, column=11, padx=5, pady=5)

    @log_function
    def create_navigation_frame(self):
        self.navigation_frame = ttk.Frame(self)
        self.navigation_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        
        ttk.Label(self.navigation_frame, text="Página:").grid(row=0, column=0, padx=5, pady=5)
        self.page_entry = ttk.Entry(self.navigation_frame, width=5)
        self.page_entry.grid(row=0, column=1, padx=5, pady=5)
        
        ttk.Label(self.navigation_frame, text="Panel:").grid(row=0, column=2, padx=5, pady=5)
        self.panel_entry = ttk.Entry(self.navigation_frame, width=5)
        self.panel_entry.grid(row=0, column=3, padx=5, pady=5)
        
        self.go_to_panel_button = ttk.Button(self.navigation_frame, text="Ir a Panel", command=self.go_to_panel)
        self.go_to_panel_button.grid(row=0, column=4, padx=5, pady=5)

    @log_function
    def load_comments(self):
        comments_file = f"{os.path.splitext(self.comic_file)[0]}_comments.json"
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
                return all_comments.get(str(self.page), "")
        return ""

    @log_function
    def save_comments(self):
        comments_file = f"{os.path.splitext(self.comic_file)[0]}_comments.json"
        comments = self.comments_text.get("1.0", tk.END).strip()
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
        else:
            all_comments = {}
        all_comments[str(self.page)] = comments
        with open(comments_file, 'w', encoding='utf-8') as f:
            json.dump(all_comments, f, ensure_ascii=False, indent=4)
        messagebox.showinfo("Guardado", "Comentarios guardados correctamente.")

    @log_function
    def create_temp_ocr(self):
        logger.debug("Iniciando la creación de la caja de texto temporal.")
        
        if self.temp_text is not None:  # Verificar si ya existe
            logger.debug("Caja de texto temporal ya existe. No se crea otra.")
            return

        self.temp_ocr = ttk.Frame(self.text_frame)
        self.temp_ocr.grid(row=4, column=0, sticky="ew", padx=5, pady=5)

        ttk.Label(self.temp_ocr, text="OCR Temporal").grid(row=0, column=0, sticky="w")
        text = tk.Text(self.temp_ocr, height=3, wrap=tk.WORD)
        text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)

        self.temp_text = text
        self.text_widgets["temp"] = {"original": text}
        logger.debug("Caja de texto temporal creada correctamente.")

    @log_function
    def detect_text_areas(self):
        img = self.panel_image.resize((self.panel_image.width * 2, self.panel_image.height * 2), Image.LANCZOS)
        gray = img.convert('L')
        thresh = gray.point(lambda x: 0 if x < 200 else 255, '1')
        bbox = thresh.getbbox()
        if bbox:
            margin = 10
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(img.width, x2 + margin)
            y2 = min(img.height, y2 + margin)
            self.text_areas.append((x1, y1, x2, y2))
            self.draw_text_area((x1, y1, x2, y2), len(self.text_areas))

    @log_function
    def delete_panel(self):
        if messagebox.askyesno("Confirmar eliminación", f"¿Está seguro de que desea eliminar el panel {self.panel + 1}?"):
            self.comic_viewer.panel_manager.delete_panel(self.page, self.panel)
            self.comic_viewer.refresh_panels()
            self.destroy()


    @log_function
    def load_saved_translation(self, index):
        filename = f"{os.path.splitext(self.comic_file)[0]}_trans.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_translations = json.load(f)
                for item in all_translations:
                    if item['page'] == self.page and item['panel'] == self.panel:
                        if index <= len(item['texts']):
                            return item['texts'][index-1]
        return None

    @log_function
    def process_text(self):
        for index, bbox in enumerate(self.text_areas, 1):
            saved_translation = self.load_saved_translation(index)
            if saved_translation:
                self._populate_widgets_with_saved_translation(index, saved_translation)
            else:
                if index in self.text_widgets:  # Verificar si el widget ya existe
                    self.text_widgets[index]["original"].delete("1.0", tk.END)
                    for lang, trans_widget in self.text_widgets[index]["translations"].items():
                        trans_widget.delete("1.0", tk.END)
                # else:
                    # No llamar a create_text_widgets si no hay traducción guardada
    
        self.clear_text_selection()

    @log_function
    def save_text(self):
        data = {
            "page": self.page,
            "panel": self.panel,
            "texts": []
        }
        for index, widgets in enumerate(self.text_widgets.values(), 1):
            if index != "temp":
                text_data = {
                    "bbox": self.text_areas[index-1],
                    "original": widgets["original"].get(1.0, tk.END).strip(),
                    "translations": {lang: widget.get(1.0, tk.END).strip()
                                     for lang, widget in widgets["translations"].items()}
                }
                data["texts"].append(text_data)

        with open(self.get_translation_file_path(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.debug("Traducciones guardadas correctamente.")

    @log_function
    def create_text_widgets(self, index):
        # Verificar si el índice ya existe
        if index in self.text_widgets:
            return  # Si ya existe, no hacer nada

        frame = ttk.Frame(self.text_frame)
        frame.grid(row=index-1, column=0, sticky="ew", pady=5)
        frame.grid_columnconfigure(0, weight=1)

        ttk.Label(frame, text=f"Globo {index}").grid(row=0, column=0, sticky="w")

        original = tk.Text(frame, height=5, wrap=tk.WORD, font=("Helvetica", 12, "bold"))
        original.grid(row=1, column=0, sticky="ew")

        translations = {}
        for i, lang in enumerate(["Español", "Inglés"]):
            trans = tk.Text(frame, height=5, wrap=tk.WORD, font=("Helvetica", 12, "bold"))
            trans.grid(row=i+2, column=0, sticky="ew")
            translations[lang] = trans

        self.text_widgets[index] = {"original": original, "translations": translations}

    @log_function
    def translate_text(self):
        api = self.api_var.get()
        for index, widgets in self.text_widgets.items():
            if "original" in widgets:
                text = widgets["original"].get(1.0, tk.END).strip()
                if api == "google":
                    self.translate_with_google(text, widgets["translations"])
                elif api == "deepl":
                    self.translate_with_deepl(text, widgets["translations"])
                elif api == "chatgpt":
                    self.translate_with_chatgpt(text, widgets["translations"])

    @log_function
    def translate_with_google(self, text, translation_widgets):
        translator = Translator()
        for lang, widget in translation_widgets.items():
            translation = translator.translate(text, dest=self.get_lang_code(lang)).text
            widget.delete(1.0, tk.END)
            widget.insert(tk.END, translation)

    @log_function
    def translate_with_deepl(self, text, translation_widgets):
        pass  # Implementar la lógica de traducción con DeepL aquí

    @log_function
    def translate_with_chatgpt(self, text, translation_widgets):
        pass  # Implementar la lógica de traducción con ChatGPT aquí

    @log_function
    def start_rectangle(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red")

    @log_function
    def draw_rectangle(self, event):
        self.canvas.coords(self.rect, self.start_x, self.start_y, event.x, event.y)

    @log_function
    def end_rectangle(self, event):
        self.text_areas.append(self.canvas.coords(self.rect))

    @log_function
    def previous_panel(self):
        self.comic_viewer.prev_panel()
        self.update_translation_editor()

    @log_function
    def next_panel(self):
        self.comic_viewer.next_panel()
        self.update_translation_editor()

    @log_function
    def increase_text_size(self):
        self._change_text_size(2)

    @log_function
    def decrease_text_size(self):
        self._change_text_size(-2)

    @log_function
    def _change_text_size(self, change):
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                current_font = widgets["original"].cget("font")
                font_name, font_size, *font_weight = current_font.split()
                font_size = int(font_size) + change
                new_font = f"{font_name} {font_size} {' '.join(font_weight)}"
                widgets["original"].configure(font=new_font)
                for trans_widget in widgets["translations"].values():
                    trans_widget.configure(font=new_font)

    @log_function
    def busqueda_web_traduccion(self):
        selected_text = self.get_selected_text()
        if selected_text:
            reverso_url = f"https://www.reverso.net/Text%C3%BCbersetzung#sl=ger&tl=spa&text={urllib.parse.quote(selected_text)}"
            deepl_url = f"https://www.deepl.com/translator#de/en/{urllib.parse.quote(selected_text)}"
            wordreference_url = f"https://www.wordreference.com/deen/{urllib.parse.quote(selected_text)}"
            
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
                f"Frase: {selected_text}"
            )
            
            pyperclip.copy(prompt)
            
            messagebox.showinfo("Información", "Se han abierto las páginas web con el prompt incluido y se ha copiado al portapapeles.")
        else:
            messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")

    @log_function
    def get_selected_text(self):
        selected_text = ""
        for widget in self.text_widgets.values():
            if "original" in widget:
                try:
                    selected_text += widget["original"].get(tk.SEL_FIRST, tk.SEL_LAST)
                except tk.TclError:
                    pass
            if "translations" in widget:
                for trans_widget in widget["translations"].values():
                    try:
                        selected_text += trans_widget.get(tk.SEL_FIRST, tk.SEL_LAST)
                    except tk.TclError:
                        pass
        if not selected_text and self.temp_text is not None:
            try:
                selected_text = self.temp_text.get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
        return selected_text

    @log_function
    def go_to_panel(self):
        try:
            page = int(self.page_entry.get()) - 1
            panel = int(self.panel_entry.get()) - 1
    
            if page < 0 or page >= self.comic_viewer.panel_manager.get_num_pages():
                raise ValueError("Página inválida")
    
            panels = self.comic_viewer.panel_manager.get_panels(page)
            if not panels or panel < 0 or panel >= len(panels):
                raise ValueError("Panel inválido")
    
            self.comic_viewer.current_page = page
            self.comic_viewer.current_panel = panel
            self.comic_viewer.show_panels()
            self.update_translation_editor()
        except ValueError:
            messagebox.showerror("Error", "No existe el panel especificado")

    @log_function
    def update_translation_editor(self):
        self.page = self.comic_viewer.current_page
        self.panel = self.comic_viewer.current_panel
        self.panel_image = self.comic_viewer.get_current_panel_image()
        self.title(f"Traducción - Página {self.page + 1}, Panel {self.panel + 1}")
        
        self.display_panel_image()
        self.adjust_image_size()

        self.text_areas = []
        self.text_widgets = {}
        self.load_saved_translations()
        self.detect_text_areas()

    @log_function
    def draw_text_area(self, bbox, index):
        x1, y1, x2, y2 = bbox
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", tags=f"area{index}")
        self.canvas.create_text(x1, y1, text=f"Globo {index}", anchor=tk.NW, tags=f"area{index}")

    @log_function
    def get_lang_code(self, lang):
        return {"Español": "es", "Inglés": "en"}.get(lang, "en")

    @log_function
    def process_text_content(self, text):
        return text  # Aquí puedes añadir tu lógica de procesamiento de texto

def main():
    root = tk.Tk()
    root.mainloop()

if __name__ == "__main__":
    main()
