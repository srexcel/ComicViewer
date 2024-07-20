import tkinter as tk
from tkinter import ttk, messagebox, simpledialog, TclError, SEL_FIRST, SEL_LAST, END
from PIL import Image, ImageTk
import pytesseract
from googletrans import Translator
import json
import os
import openai
import urllib.parse
import pyperclip
import webbrowser
import cv2
import numpy as np

class TranslationEditor:
    def __init__(self, root, master, parent, comic_viewer, current_page, panel_image, current_panel, input_file, page, panel, comic_file, translation_config):
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

        self.top = tk.Toplevel(master)
        self.top.title(f"Traducción - Página {page + 1}, Panel {panel + 1}")

        self.text_widgets = {
            'original': tk.Text(self.master),  # Suponiendo que self.master es el contenedor principal
            'translations': {}
        }
        self.translations = {}
        self.temp_ocr = None
        self.comments = self.load_comments()

        self.text_areas = []  # Inicializar text_areas
        self.text_widgets = {}
        self.translations = {}
        self.temp_ocr = None
        self.comments = self.load_comments()

        self.create_ui()  # Primero creamos la UI
        self.load_saved_translations()
        self.detect_text_areas()
        self.load_api_keys()
        self.adjust_window_size()  # Luego ajustamos el tamaño de la ventana
        self.bind_events()

    def create_ui(self):
        self.top.grid_columnconfigure(0, weight=1)
        self.top.grid_rowconfigure(0, weight=1)
        
        # Frame principal
        self.main_frame = ttk.PanedWindow(self.top, orient=tk.HORIZONTAL)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        
        # Frame para la imagen
        self.image_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.image_frame, weight=1)
    
        # Canvas para la imagen con barras de desplazamiento
        self.canvas = tk.Canvas(self.image_frame)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        self.x_scrollbar = ttk.Scrollbar(self.image_frame, orient="horizontal", command=self.canvas.xview)
        self.x_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.y_scrollbar = ttk.Scrollbar(self.image_frame, orient="vertical", command=self.canvas.yview)
        self.y_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.canvas.configure(xscrollcommand=self.x_scrollbar.set, yscrollcommand=self.y_scrollbar.set)
    
        # Frame para los textos
        self.text_frame = ttk.Frame(self.main_frame)
        self.main_frame.add(self.text_frame, weight=1)
        
        # Configurar el grid del text_frame
        self.text_frame.grid_columnconfigure(0, weight=1)
        self.text_frame.grid_rowconfigure(2, weight=1)  # La fila de comentarios crecerá
        
        # Cajas de texto
        self.original_text = tk.Text(self.text_frame, wrap=tk.WORD, height=10)
        self.original_text.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        
        self.translation_text = tk.Text(self.text_frame, wrap=tk.WORD, height=10)
        self.translation_text.grid(row=1, column=0, sticky="ew", padx=5, pady=5)
        
        self.comments_text = tk.Text(self.text_frame, wrap=tk.WORD)
        self.comments_text.grid(row=2, column=0, sticky="nsew", padx=5, pady=5)
        
        # Frame para los botones
        self.button_frame = ttk.Frame(self.top)
        self.button_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        self.process_button = ttk.Button(self.button_frame, text="Procesar", command=self.process_text)
        self.process_button.pack(side=tk.LEFT)
        
        self.save_button = ttk.Button(self.button_frame, text="Guardar", command=self.save_text)
        self.save_button.pack(side=tk.LEFT)
        
        self.api_var = tk.StringVar()
        self.api_var.set("google")  # Valor predeterminado
        
        self.api_menu = ttk.OptionMenu(
            self.button_frame, self.api_var, "google", "google", "deepl", "chatgpt"
        )
        self.api_menu.pack(side=tk.LEFT)
        
        self.translate_button = ttk.Button(self.button_frame, text="Traducir", command=self.translate_text)
        self.translate_button.pack(side=tk.LEFT)
        
        self.ocr_button = ttk.Button(self.button_frame, text="OCR", command=self.create_temp_ocr)
        self.ocr_button.pack(side=tk.LEFT)
        
        self.previous_panel_button = ttk.Button(self.button_frame, text="Panel Anterior", command=self.previous_panel)
        self.previous_panel_button.pack(side=tk.LEFT)
        
        self.next_panel_button = ttk.Button(self.button_frame, text="Siguiente Panel", command=self.next_panel)
        self.next_panel_button.pack(side=tk.LEFT)
        
        self.increase_text_size_button = ttk.Button(self.button_frame, text="Aumentar tamaño de texto", command=self.increase_text_size)
        self.increase_text_size_button.pack(side=tk.LEFT)
        
        self.decrease_text_size_button = ttk.Button(self.button_frame, text="Disminuir tamaño de texto", command=self.decrease_text_size)
        self.decrease_text_size_button.pack(side=tk.LEFT)
        
        # Nuevos botones
        self.busqueda_web_traduccion_button = ttk.Button(self.button_frame, text="Búsqueda web", command=self.busqueda_web_traduccion)
        self.busqueda_web_traduccion_button.pack(side=tk.LEFT)
        
        self.delete_panel_button = ttk.Button(self.button_frame, text="Borrar panel", command=self.delete_panel)
        self.delete_panel_button.pack(side=tk.LEFT)
        
        self.reprocess_ocr_button = ttk.Button(self.button_frame, text="Reprocesar OCR", command=self.reprocess_ocr)
        self.reprocess_ocr_button.pack(side=tk.LEFT)
    
        # Frame para el desplazamiento rápido
        self.navigation_frame = ttk.Frame(self.top)
        self.navigation_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=10)
        
        ttk.Label(self.navigation_frame, text="Página:").pack(side=tk.LEFT)
        self.page_entry = ttk.Entry(self.navigation_frame, width=5)
        self.page_entry.pack(side=tk.LEFT)
        
        ttk.Label(self.navigation_frame, text="Panel:").pack(side=tk.LEFT)
        self.panel_entry = ttk.Entry(self.navigation_frame, width=5)
        self.panel_entry.pack(side=tk.LEFT)
        
        self.go_to_panel_button = ttk.Button(self.navigation_frame, text="Ir a Panel", command=self.go_to_panel)
        self.go_to_panel_button.pack(side=tk.LEFT)
    
        # Mostrar la imagen
        self.photo = ImageTk.PhotoImage(self.panel_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))
        
        self.canvas.bind("<Button-1>", self.start_rectangle)
        self.canvas.bind("<B1-Motion>", self.draw_rectangle)
        self.canvas.bind("<ButtonRelease-1>", self.end_rectangle)
        
        # Añadir sección de comentarios
        self.comments_frame = ttk.Frame(self.text_frame)
        self.comments_frame.grid(row=len(self.text_widgets) + 1, column=0, sticky="ew", pady=5)
    
        ttk.Label(self.comments_frame, text="Comentarios:").grid(row=0, column=0, sticky="w")
        self.comments_text = tk.Text(self.comments_frame, height=5, wrap=tk.WORD)
        self.comments_text.grid(row=1, column=0, sticky="ew")
        self.comments_text.insert(tk.END, self.comments)
    
        save_comments_button = ttk.Button(self.comments_frame, text="Guardar Comentarios", command=self.save_comments)
        save_comments_button.grid(row=2, column=0, sticky="e", pady=5)
    
        # Vincular evento de redimensionamiento
        self.top.bind("<Configure>", self.on_window_resize)
        
        # Ajustar el tamaño inicial de la ventana
        self.top.update_idletasks()
        screen_width = self.top.winfo_screenwidth()
        screen_height = self.top.winfo_screenheight()
        window_width = min(self.top.winfo_reqwidth(), screen_width * 0.8)
        window_height = min(self.top.winfo_reqheight(), screen_height * 0.8)
        self.top.geometry(f"{int(window_width)}x{int(window_height)}")

    def adjust_window_size(self):
        panel_width = self.panel_image.width
        panel_height = self.panel_image.height
        
        desired_width = panel_width + 400
        desired_height = panel_height + 100
        
        self.top.geometry(f"{desired_width}x{desired_height}")
        
        self.canvas.config(width=panel_width, height=panel_height)
        self.canvas.config(scrollregion=(0, 0, panel_width, panel_height))
        self.on_window_resize(None)  # Llamar a on_window_resize para ajustar inicialmente los tamaños

    def on_window_resize(self, event):
        if event is None:
            # Proporcionar valores predeterminados para width y height si event es None
            width, height = self.master.winfo_width(), self.master.winfo_height()
        else:
            width, height = event.width, event.height

        new_height = max(10, (height - 200) // 3)  # 200 es un valor aproximado para el espacio de botones y márgenes
        new_width = max(10, (width - 20) // 2)  # Ajuste para el nuevo ancho de los widgets

        if 'original' in self.text_widgets:
            self.text_widgets['original'].place(x=10, y=10, width=new_width, height=new_height)
        else:
            print("Error: 'original' key not found in self.text_widgets")

        for i, (lang, widget) in enumerate(self.text_widgets['translations'].items()):
            widget.place(x=new_width + 20, y=10 + (new_height + 10) * i, width=new_width, height=new_height)

    def bind_events(self):
        self.top.bind("<Configure>", self.on_window_resize)

    def create_temp_ocr(self):
        if self.temp_ocr:
            self.temp_ocr.destroy()
    
        self.temp_ocr = ttk.Frame(self.text_frame)
        self.temp_ocr.grid(row=len(self.text_widgets), column=0, sticky="ew", pady=5)
    
        ttk.Label(self.temp_ocr, text="OCR Temporal").grid(row=0, column=0, sticky="w")
        text = tk.Text(self.temp_ocr, height=3, wrap=tk.WORD)
        text.grid(row=1, column=0, sticky="ew")
    
        self.text_widgets["temp"] = {"original": text}
    
        self.canvas.bind("<ButtonPress-1>", self.start_temp_ocr)
        self.canvas.bind("<ButtonRelease-1>", self.end_temp_ocr)

        # Nuevos botones
        self.increase_button = ttk.Button(self.temp_ocr, text="Aumentar", command=self.increase_image)
        self.increase_button.grid(row=2, column=0, sticky="w", pady=5)
        
        self.auto_adjust_button = ttk.Button(self.temp_ocr, text="Autoajustar", command=self.auto_adjust_image)
        self.auto_adjust_button.grid(row=2, column=1, sticky="w", pady=5)

        self.ocr_attempts = 0
        self.current_scale = 1.0
    
    def end_temp_ocr(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
    
        # Convertir las coordenadas del canvas a las coordenadas de la imagen original
        start_x, start_y = self.canvas_to_image_coords(self.start_x, self.start_y)
        end_x, end_y = self.canvas_to_image_coords(end_x, end_y)
    
        bbox = (min(start_x, end_x), min(start_y, end_y), max(start_x, end_x), max(start_y, end_y))
        
        self.perform_ocr(bbox)

    def perform_ocr(self, bbox):
        cropped = self.panel_image.crop(bbox)
        img_np = np.array(cropped)
        
        # Aplicar escala
        new_size = (int(img_np.shape[1] * self.current_scale), int(img_np.shape[0] * self.current_scale))
        img_np = cv2.resize(img_np, new_size, interpolation=cv2.INTER_CUBIC)
        
        # Realizar OCR
        text = pytesseract.image_to_string(Image.fromarray(img_np))
        
        if not text.strip():
            self.ocr_attempts += 1
            if self.ocr_attempts < 4:
                if messagebox.askyesno("OCR", "No encontré nada, ¿intento nuevamente a mayor resolución?"):
                    self.current_scale *= 2
                    self.perform_ocr(bbox)
                else:
                    self.reset_ocr()
            else:
                messagebox.showinfo("OCR", "No fue posible identificar texto")
                self.reset_ocr()
        else:
            processed_text = self.process_text_content(text)
            self.text_widgets["temp"]["original"].delete(1.0, tk.END)
            self.text_widgets["temp"]["original"].insert(tk.END, processed_text)
            self.reset_ocr()

    def reset_ocr(self):
        self.ocr_attempts = 0
        self.current_scale = 1.0
        self.canvas.unbind("<ButtonPress-1>")
        self.canvas.unbind("<ButtonRelease-1>")

    def increase_image(self):
        self.current_scale *= 2
        self.update_image()

    def auto_adjust_image(self):
        self.current_scale = 1.0
        self.update_image()

    def update_image(self):
        # Redimensionar la imagen
        new_size = (int(self.panel_image.width * self.current_scale), 
                    int(self.panel_image.height * self.current_scale))
        resized_image = self.panel_image.copy()
        resized_image = resized_image.resize(new_size, Image.LANCZOS)
        
        # Actualizar el canvas
        self.photo = ImageTk.PhotoImage(resized_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def increase_text_size(self):
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                current_font = widgets["original"].cget("font")
                font_name, font_size, *font_weight = current_font.split()
                font_size = int(font_size) + 2
                new_font = f"{font_name} {font_size} {' '.join(font_weight)}"
                widgets["original"].configure(font=new_font)
                for lang, trans_widget in widgets["translations"].items():
                    trans_widget.configure(font=new_font)
        self.comments_text.configure(font=new_font)  # Aplicar el cambio a la caja de comentarios
    
    def decrease_text_size(self):
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                current_font = widgets["original"].cget("font")
                font_name, font_size, *font_weight = current_font.split()
                font_size = int(font_size) - 2
                new_font = f"{font_name} {font_size} {' '.join(font_weight)}"
                widgets["original"].configure(font=new_font)
                for lang, trans_widget in widgets["translations"].items():
                    trans_widget.configure(font=new_font)
        self.comments_text.configure(font=new_font)  # Aplicar el cambio a la caja de comentarios

    def calculate_dpi(self, img):
        # Estimar el DPI basado en el tamaño de la imagen
        # Esta es una estimación aproximada, puedes ajustarla según tus necesidades
        height, width = img.shape[:2]
        diagonal_pixels = np.sqrt(width**2 + height**2)
        diagonal_inches = 5  # Asumimos que la diagonal es de 5 pulgadas, ajusta según sea necesario
        return diagonal_pixels / diagonal_inches

    def busqueda_web_traduccion(self):
        try:
            selection = self.translation_text.get(SEL_FIRST, SEL_LAST)
        except TclError:
            selection = None
        if selection:
            # Abrir los sitios web con la selección
            webbrowser.open("https://www.reverso.net/Text%C3%BCbersetzung#sl=ger&tl=spa&text={urllib.parse.quote(selection)}")
            webbrowser.open(f"https://www.deepl.com/translator#de/en/{urllib.parse.quote(selection)}")
            webbrowser.open(f"https://www.wordreference.com/deen/{urllib.parse.quote(selection)}")
            
            # Crear el prompt
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
            
            # Codificar el prompt para la URL
            encoded_prompt = urllib.parse.quote(prompt)
            
            # Abrir ChatGPT y Poe con el prompt en la URL
            webbrowser.open(f"https://chat.openai.com/?model=text-davinci-002-render-sha&prompt={encoded_prompt}")
            webbrowser.open(f"https://poe.com/ChatGPT?prompt={encoded_prompt}")
            
            messagebox.showinfo("Información", "Se han abierto las páginas web con el prompt incluido y se ha copiado al portapapeles.")
        else:
            messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")

    def display_panel_image(self):
        # Método para mostrar la imagen del panel
        image = Image.open(self.panel_image)
        photo = ImageTk.PhotoImage(image)
        self.panel_image_label.config(image=photo)
        self.panel_image_label.image = photo  # Guardar referencia de la imagen para evitar que se recoja por el GC

    def web_search(self):
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

    def translate_with_claude(self):
        if not hasattr(self, 'claude_client') or self.claude_client is None:
            self.prompt_for_api_key("claude")
            return  # Salir y esperar a que el usuario ingrese la API key
    
    def translate_text(self):
        api = self.api_var.get()
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                text = widgets["original"].get(1.0, tk.END).strip()
                if api == "google":
                    self.translate_with_google(text)
                elif api == "deepl":
                    self.translate_with_deepl(text)
                elif api == "chatgpt":
                    self.translate_with_chatgpt(text)
                elif api == "claude":
                    self.translate_with_claude()

    def load_api_keys(self):
        try:
            with open('KEYS.json', 'r') as f:
                self.api_keys = json.load(f)
            if 'chatgpt' in self.api_keys:
                openai.api_key = self.api_keys['chatgpt'].get('api_key')
        except FileNotFoundError:
            self.api_keys = {}

    def translate_with_deepl(self, text):
        import requests
    
        if "deepl" not in self.api_keys or not self.api_keys["deepl"]["api_key"]:
            messagebox.showwarning("Falta API Key", "No tienes una API Key de DeepL configurada.")
            return
    
        url = "https://api-free.deepl.com/v2/translate"
        headers = {
            "Authorization": f"DeepL-Auth-Key {self.api_keys['deepl']['api_key']}"
        }
    
        def deepl_translate(text, target_lang):
            params = {
                "text": text,
                "target_lang": target_lang.upper()
            }
            response = requests.post(url, headers=headers, data=params)
            if response.status_code == 200:
                result = response.json()
                return result['translations'][0]['text']
            else:
                return "Error: " + response.text
    
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                for lang, trans_widget in widgets["translations"].items():
                    translation = deepl_translate(text, self.get_lang_code(lang))
                    trans_widget.delete(1.0, tk.END)
                    trans_widget.insert(tk.END, translation)

    def perform_translation(self, translator, text):
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                for lang, trans_widget in widgets["translations"].items():
                    translation = translator.translate(text, dest=self.get_lang_code(lang)).text
                    trans_widget.delete(1.0, tk.END)
                    trans_widget.insert(tk.END, translation)

    def translate_with_google(self, text):
        translator = Translator()
        self.perform_translation(translator, text)

    def translate_with_chatgpt(self, text):
        if not openai.api_key:
            self.prompt_for_api_key("chatgpt")
    
        def chatgpt_translate(text, target_lang):
            try:
                response = openai.ChatCompletion.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": f"You are a translator. Translate the following text to {target_lang}."},
                        {"role": "user", "content": text}
                    ]
                )
                return response.choices[0].message['content'].strip()
            except openai.error.AuthenticationError:
                self.prompt_for_api_key("chatgpt")
                return "Error: Incorrect API key"
            except Exception as e:
                return f"Error: {str(e)}"
    
        for widgets in self.text_widgets.values():
            if "original" in widgets:
                for lang, trans_widget in widgets["translations"].items():
                    translation = chatgpt_translate(text, self.get_lang_code(lang))
                    trans_widget.delete('1.0', tk.END)
                    trans_widget.insert(tk.END, translation)

    def open_comments_window(self):
        comments_window = tk.Toplevel(self.top)
        comments_window.title("Comentarios")
        
        # Obtener el tamaño actual de la ventana de texto de panel
        window_width = self.top.winfo_width() * 2
        window_height = self.top.winfo_height() * 2
        
        # Establecer el tamaño para la ventana de comentarios (doble del tamaño actual)
        comments_window.geometry(f"{window_width}x{window_height}")

        comments_text = tk.Text(comments_window, wrap=tk.WORD, font=("Arial", 12), bg='white', fg='black')
        comments_text.pack(expand=1, fill=tk.BOTH)

        comments_scrollbar = tk.Scrollbar(comments_window, orient=tk.VERTICAL, command=comments_text.yview)
        comments_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        comments_text.configure(yscrollcommand=comments_scrollbar.set)

        comments_text.insert(tk.END, self.comments)

        def save_comments():
            self.comments = comments_text.get(1.0, tk.END).strip()
            self.save_comments()
            comments_window.destroy()

        save_button = tk.Button(comments_window, text="Guardar comentarios", command=save_comments)
        save_button.pack(fill=tk.X)

        close_button = tk.Button(comments_window, text="Cerrar", command=comments_window.destroy)
        close_button.pack(fill=tk.X)

    def load_saved_translations(self):
        filename = f"{os.path.splitext(self.comic_file)[0]}_trans.json"
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                all_translations = json.load(f)
                for translation in all_translations:
                    if translation['page'] == self.page and translation['panel'] == self.panel:
                        self.saved_translations = translation['texts']
                        self.populate_text_widgets()
                        return
        self.saved_translations = []
    
    def populate_text_widgets(self):
        for i, text_data in enumerate(self.saved_translations, 1):
            if i not in self.text_widgets:
                self.create_text_widgets(i)
            
            self.text_widgets[i]["original"].delete("1.0", tk.END)
            self.text_widgets[i]["original"].insert(tk.END, text_data['original'])
            
            for lang, trans in text_data['translations'].items():
                self.text_widgets[i]["translations"][lang].delete("1.0", tk.END)
                self.text_widgets[i]["translations"][lang].insert(tk.END, trans)
            
    def reprocess_ocr(self):
        selected_text = self.get_selected_text()
        if selected_text:
            original_language = self.translation_config.get('languages', {}).get('original', 'desconocido')
            prompt = f"Este texto es el resultado de un OCR de un comic en {original_language}, deduce el OCR correcto y traduce al ing esp ger:\n{selected_text}"
            pyperclip.copy(prompt)
            
            # Mostrar opciones de servicios para abrir
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

    def load_comments(self):
        comments_file = f"{os.path.splitext(self.comic_file)[0]}_comments.json"
        if os.path.exists(comments_file):
            with open(comments_file, 'r', encoding='utf-8') as f:
                all_comments = json.load(f)
                return all_comments.get(str(self.page), "")
        return ""

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
        
    def delete_panel(self):
        if messagebox.askyesno("Confirmar eliminación", f"¿Está seguro de que desea eliminar el panel {self.panel + 1}?"):
            self.comic_viewer.panel_manager.delete_panel(self.page, self.panel)
            self.comic_viewer.refresh_panels()
            self.top.destroy()

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
        if not selected_text:
            try:
                selected_text = self.temp_ocr["original"].get(tk.SEL_FIRST, tk.SEL_LAST)
            except tk.TclError:
                pass
        return selected_text
        
    def process_text(self):
        print("Process button clicked")
        for index, bbox in enumerate(self.text_areas, 1):
            print(f"Processing text area {index} with bbox {bbox}")
            if index not in self.text_widgets:
                self.create_text_widgets(index)
        for index, bbox in enumerate(self.text_areas, 1):   
            if index not in self.text_widgets:
                self.create_text_widgets(index)
            
            # Intentar cargar traducciones guardadas
            saved_translation = self.load_saved_translation(index)
            if saved_translation:
                self.text_widgets[index]["original"].delete(1.0, tk.END)
                self.text_widgets[index]["original"].insert(tk.END, saved_translation['original'])
                for lang, trans in saved_translation['translations'].items():
                    self.text_widgets[index]["translations"][lang].delete(1.0, tk.END)
                    self.text_widgets[index]["translations"][lang].insert(tk.END, trans)
            else:
                # Si no hay traducción guardada, procesar el OCR
                cropped = self.panel_image.crop(bbox)
                text = pytesseract.image_to_string(cropped)
                processed_text = self.process_text_content(text)
                self.text_widgets[index]["original"].delete(1.0, tk.END)
                self.text_widgets[index]["original"].insert(tk.END, processed_text)

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
    
    def create_text_widgets(self, index):
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

    def detect_text_areas(self):
        # Aumentar la resolución de la imagen
        img = self.panel_image.resize((self.panel_image.width * 2, self.panel_image.height * 2), Image.LANCZOS)
        
        # Convertir a escala de grises
        gray = img.convert('L')
        
        # Aplicar umbral
        thresh = gray.point(lambda x: 0 if x < 200 else 255, '1')
        
        # Detectar la caja delimitadora
        bbox = thresh.getbbox()
        if bbox:
            # Ampliar la caja delimitadora
            margin = 10  # Ajustar este valor según sea necesario
            x1, y1, x2, y2 = bbox
            x1 = max(0, x1 - margin)
            y1 = max(0, y1 - margin)
            x2 = min(img.width, x2 + margin)
            y2 = min(img.height, y2 + margin)
            
            # Agregar el área de texto detectada
            self.text_areas.append((x1, y1, x2, y2))
            self.draw_text_area((x1, y1, x2, y2), len(self.text_areas))

    def draw_text_area(self, bbox, index):
        x1, y1, x2, y2 = bbox
        self.canvas.create_rectangle(x1, y1, x2, y2, outline="red", tags=f"area{index}")
        self.canvas.create_text(x1, y1, text=f"Globo {index}", anchor=tk.NW, tags=f"area{index}")

    def start_rectangle(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)

    def draw_rectangle(self, event):
        cur_x = self.canvas.canvasx(event.x)
        cur_y = self.canvas.canvasy(event.y)
        self.canvas.delete("temp_rect")
        self.canvas.create_rectangle(self.start_x, self.start_y, cur_x, cur_y, outline="blue", tags="temp_rect")

    def end_rectangle(self, event):
        end_x = self.canvas.canvasx(event.x)
        end_y = self.canvas.canvasy(event.y)
        self.canvas.delete("temp_rect")
        bbox = (min(self.start_x, end_x), min(self.start_y, end_y), max(self.start_x, end_x), max(self.start_y, end_y))
        self.text_areas.append(bbox)
        self.draw_text_area(bbox, len(self.text_areas))

    def save_text(self):
        data = {
            "page": self.page,
            "panel": self.panel,
            "texts": []
        }
        for index, widgets in self.text_widgets.items():
            if index != "temp":
                text_data = {
                    "bbox": self.text_areas[index-1],
                    "original": widgets["original"].get(1.0, tk.END).strip(),
                    "translations": {lang: widget.get(1.0, tk.END).strip() 
                                     for lang, widget in widgets["translations"].items()}
                }
                data["texts"].append(text_data)
        filename = f"{os.path.splitext(self.comic_file)[0]}_trans.json"
        try:
            with open(filename, 'r+') as f:
                file_data = json.load(f)
                updated = False
                for i, item in enumerate(file_data):
                    if item['page'] == self.page and item['panel'] == self.panel:
                        file_data[i] = data
                        updated = True
                        break
                if not updated:
                    file_data.append(data)
                f.seek(0)
                json.dump(file_data, f, indent=4)
                f.truncate()
        except FileNotFoundError:
            with open(filename, 'w') as f:
                json.dump([data], f, indent=4)
        messagebox.showinfo("Guardado", "Texto guardado exitosamente")

    def create_additional_translation_boxes(self):
        for index, widgets in self.text_widgets.items():
            if "original" in widgets:
                for lang in ["Español", "Inglés"]:
                    if lang not in widgets["translations"]:
                        trans = tk.Text(self.text_frame, height=6, wrap=tk.WORD, font=("Arial", 12, "bold"))
                        trans.insert(tk.END, f"{lang} (ChatGPT):")
                        trans.grid(row=index * 2, column=1, sticky="ew")
                        widgets["translations"][lang] = trans

    def get_lang_code(self, lang):
        return {"Español": "es", "Inglés": "en"}.get(lang, "en")

    def process_text_content(self, text):
        lines = text.split('\n')
        processed_text = []
        for i, line in enumerate(lines):
            words = line.split()
            for j, word in enumerate(words):
                if word.endswith('-') and i + 1 < len(lines):
                    next_line_words = lines[i + 1].split()
                    if next_line_words:
                        word = word[:-1] + next_line_words[0]
                        del next_line_words[0]
                        lines[i + 1] = ' '.join(next_line_words)
                processed_text.append(word)
        
        return ' '.join(processed_text)

    def next_panel(self):
        next_page = self.page
        next_panel = self.panel + 1
        
        if next_panel >= len(self.comic_viewer.panel_images):
            next_page += 1
            next_panel = 0

        if next_page >= self.comic_viewer.panel_manager.get_num_pages():
            messagebox.showinfo("Fin del archivo", "Has llegado al final del archivo.")
            return

        if not self.comic_viewer.panel_manager.get_panels(next_page):
            messagebox.showinfo("No hay paneles", f"No hay paneles en la página {next_page + 1}.")
            self.comic_viewer.show_page(next_page)
            return

        self.comic_viewer.current_page = next_page
        self.comic_viewer.current_panel = next_panel
        self.comic_viewer.show_panels()
        self.update_translation_editor()

    def update_translation_editor(self):
        self.page = self.comic_viewer.current_page
        self.panel = self.comic_viewer.current_panel
        self.panel_image = self.comic_viewer.get_current_panel_image()
        self.top.title(f"Traducción - Página {self.page + 1}, Panel {self.panel + 1}")
        
        self.photo = ImageTk.PhotoImage(self.panel_image)
        self.canvas.delete("all")
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        
        self.adjust_window_size()

        self.text_areas = []
        self.text_widgets = {}
        self.load_saved_translations()
        self.detect_text_areas()

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
    
    def previous_panel(self):
        self.comic_viewer.prev_panel()
        self.panel_image = self.comic_viewer.get_current_panel_image()
        self.photo = ImageTk.PhotoImage(self.panel_image)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

                    
    def adjust_image_size(self):
        # Obtener el tamaño actual del frame de la imagen
        frame_width = self.image_frame.winfo_width()
        frame_height = self.image_frame.winfo_height()
    
        # Verificar si el frame tiene un tamaño válido
        if frame_width <= 0 or frame_height <= 0:
            print(f"Frame size invalid: {frame_width}x{frame_height}")
            return
    
        # Calcular el nuevo tamaño de la imagen manteniendo la proporción
        img_ratio = self.panel_image.width / self.panel_image.height
        frame_ratio = frame_width / frame_height
    
        if img_ratio > frame_ratio:
            new_width = frame_width
            new_height = int(new_width / img_ratio)
        else:
            new_height = frame_height
            new_width = int(new_height * img_ratio)
    
        # Verificar si el nuevo tamaño es válido
        if new_width <= 0 or new_height <= 0:
            print(f"New size invalid: {new_width}x{new_height}")
            return
    
        # Redimensionar la imagen
        resized_image = self.panel_image.copy()
        resized_image.thumbnail((new_width, new_height), Image.LANCZOS)
        self.photo = ImageTk.PhotoImage(resized_image)
    
        # Actualizar el canvas
        self.canvas.delete("all")
        self.canvas.config(width=frame_width, height=frame_height)
        self.canvas.create_image(frame_width//2, frame_height//2, anchor=tk.CENTER, image=self.photo)
        self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

    def start_temp_ocr(self, event):
        self.start_x = self.canvas.canvasx(event.x)
        self.start_y = self.canvas.canvasy(event.y)
    

    
    def canvas_to_image_coords(self, canvas_x, canvas_y):
        # Obtener el tamaño actual del canvas y de la imagen
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width, image_height = self.panel_image.size
    
        # Calcular la escala
        scale_x = image_width / canvas_width
        scale_y = image_height / canvas_height
    
        # Convertir las coordenadas
        image_x = int(canvas_x * scale_x)
        image_y = int(canvas_y * scale_y)
    
        return image_x, image_y

    def busqueda_web_texto_panel(self):
        try:
            selection = self.translation_text.get(SEL_FIRST, SEL_LAST)
        except TclError:
            selection = None
        if selection:
            webbrowser.open(f"https://www.deepl.com/translator#de/en/{urllib.parse.quote(selection)}")
            webbrowser.open(f"https://www.reverso.net/text_translation.aspx?lang=DE&dir=de-es&text={urllib.parse.quote(selection)}")
            webbrowser.open(f"https://www.wordreference.com/deen/{urllib.parse.quote(selection)}")
            
            # Crear el prompt
            prompt = (
                f"Traduce y explica la siguiente frase del alemán al español:\n\n"
                f"{selection}\n\n"
                "Instrucciones:\n"
                "1. Proporciona una traducción precisa y literal.\n"
                "2. Desglosa y analiza la gramática y estructura de la frase.\n"
                "3. Identifica y explica las palabras compuestas.\n"
                "4. Proporciona ejemplos adicionales para clarificar el uso de términos y estructuras gramaticales."
            )
            
            # Codificar el prompt para la URL
            encoded_prompt = urllib.parse.quote(prompt)
            
            # Abrir ChatGPT y Poe con el prompt en la URL
            webbrowser.open(f"https://chat.openai.com/chat?input={encoded_prompt}")
            webbrowser.open(f"https://poe.com/ChatGPT?prompt={encoded_prompt}")
            
            messagebox.showinfo("Información", "Se han abierto las páginas web con el prompt incluido y se ha copiado al portapapeles.")
        else:
            messagebox.showinfo("Información", "Por favor, seleccione un texto primero.")


    class ApiKeyDialog(tk.Toplevel):
        def __init__(self, parent, service):
            super().__init__(parent)
            self.title(f"API Key for {service.capitalize()}")
            self.service = service
            self.geometry("400x100")
            self.resizable(False, False)
            
            self.label = tk.Label(self, text=f"Please enter your API key for {service.capitalize()}:")
            self.label.pack(pady=10)
            
            self.entry = tk.Entry(self, show="*")
            self.entry.pack(pady=5)
            self.entry.focus_set()
            
            self.button = tk.Button(self, text="Submit", command=self.on_submit)
            self.button.pack(pady=5)
            
            self.protocol("WM_DELETE_WINDOW", self.on_close)
            self.transient(parent)
            self.grab_set()
            self.wait_window(self)
    
        def on_submit(self):
            self.api_key = self.entry.get()
            self.destroy()
    
        def on_close(self):
            self.api_key = None
            self.destroy()




