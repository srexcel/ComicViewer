import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
import pytesseract
from googletrans import Translator as GoogleTranslator
import logging
import requests
from translation_configurator import TranslationManager as ConfiguredTranslationManager, TranslationConfiguratorApp
import platform
from utils import load_api_keys, save_api_keys, validate_api_key
import os
import openai
from deepl import Translator as DeepLTranslator
from tkinter import font as tkfont
import json

def setup_logger():
    logging.basicConfig(filename='comic_viewer.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('ComicViewer')
    logger.info("System Information:")
    logger.info(f"Python version: {platform.python_version()}")
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

class TranslationManager:
    @log_function
    def __init__(self, viewer, panel_manager):
        self.viewer = viewer
        self.panel_manager = panel_manager
        self.service_config = {
            "service": "GoogleTranslate",
            "api_key": ""
        }
        self.translator = GoogleTranslator()
        self.config = self.load_and_validate_keys()
        self.service_order = self.config.get('service_order', ['GoogleTranslate'])
        self.setup_translators()

    @log_function
    def get_current_service(self):
        return self.service_config["service"]

    @log_function
    def get_available_services(self):
        return ["GoogleTranslate", "DeepL", "ChatGPT"]

    @log_function
    def set_service_config(self, service, api_key):
        self.service_config["service"] = service
        self.service_config["api_key"] = api_key

    @log_function
    def start_translation(self, page, panel, image):
        service = self.service_config["service"]
        api_key = self.service_config["api_key"]

        # Implementar la lógica de traducción para cada servicio
        if service == "GoogleTranslate":
            self.translate_with_google(image, api_key)
        elif service == "DeepL":
            self.translate_with_deepl(image, api_key)
        elif service == "ChatGPT":
            self.translate_with_chatgpt(image, api_key)

    @log_function
    def translate_with_google(self, image, api_key):
        # Implementar traducción con Google Translate
        pass

    @log_function
    def translate_with_deepl(self, image, api_key):
        # Implementar traducción con DeepL
        pass

    @log_function
    def translate_with_chatgpt(self, image, api_key):
        # Implementar traducción con ChatGPT
        pass

    @log_function
    def perform_ocr(self):
        try:
            text = pytesseract.image_to_string(self.panel_image, lang='eng+spa+deu')
            boxes = pytesseract.image_to_data(self.panel_image, lang='eng+spa+deu', output_type=pytesseract.Output.DICT)
            
            required_keys = ['text', 'conf', 'left', 'top', 'width', 'height']
            if not all(key in boxes for key in required_keys):
                logger.error(f"OCR output is missing required keys: {boxes.keys()}")
                messagebox.showerror("Error OCR", "No se pudo extraer texto de la imagen.")
                return []
    
            text_groups = []
            for i in range(len(boxes['text'])):
                if int(boxes['conf'][i]) > 60:
                    text_groups.append({
                        'text': boxes['text'][i],
                        'box': (boxes['left'][i], boxes['top'][i], boxes['left'][i] + boxes['width'][i], boxes['top'][i] + boxes['height'][i]),
                        'group': len(text_groups) + 1
                    })
            
            return text_groups
        except Exception as e:
            logger.error(f"Error performing OCR: {e}", exc_info=True)
            messagebox.showerror("Error OCR", f"Ocurrió un error durante la extracción de texto: {e}")
            return []

    @log_function
    def translate_texts(self):
        try:
            source_lang = self.languages[0]
            target_lang1 = self.languages[1]
            target_lang2 = self.languages[2]
    
            for i, (original, trans1, trans2) in enumerate(self.text_widgets):
                try:
                    text = original.get()
                    try:
                        translation1_response = self.translator.translate(text, src=self.get_google_lang(source_lang), dest=self.get_google_lang(target_lang1))
                        translation2_response = self.translator.translate(text, src=self.get_google_lang(source_lang), dest=self.get_google_lang(target_lang2))
                    except requests.exceptions.RequestException as e:
                        logger.error(f"Network error translating group {i+1}: {e}", exc_info=True)
                        messagebox.showerror("Error de red", f"Ocurrió un error de red durante la traducción del grupo {i+1}: {str(e)}")
                        continue
    
                    if not translation1_response or not hasattr(translation1_response, 'text'):
                        logger.error(f"Invalid translation response for group {i+1}, target language 1: {translation1_response}")
                        messagebox.showerror("Error de traducción", f"Ocurrió un error durante la traducción del grupo {i+1} al primer idioma de destino.")
                        continue
    
                    if not translation2_response or not hasattr(translation2_response, 'text'):
                        logger.error(f"Invalid translation response for group {i+1}, target language 2: {translation2_response}")
                        messagebox.showerror("Error de traducción", f"Ocurrió un error durante la traducción del grupo {i+1} al segundo idioma de destino.")
                        continue
    
                    translation1 = translation1_response.text
                    translation2 = translation2_response.text
    
                    trans1.delete(0, tk.END)
                    trans1.insert(0, translation1)
                    trans2.delete(0, tk.END)
                    trans2.insert(0, translation2)
    
                    self.save_translation(self.current_page, self.current_panel, i+1, 
                                          text, source_lang, target_lang1, translation1, target_lang2, translation2)
                except Exception as e:
                    logger.error(f"Error translating group {i+1}: {e}", exc_info=True)
                    messagebox.showerror("Error de traducción", f"Ocurrió un error durante la traducción del grupo {i+1}: {str(e)}")
        except Exception as e:
            logger.error(f"Error in translate_texts: {e}", exc_info=True)
            messagebox.showerror("Error de traducción", f"Ocurrió un error al traducir los textos: {str(e)}")
            

    def load_and_validate_keys(self):
        if not os.path.exists('KEYS.json'):
            save_api_keys({})
            return {}
        
        config = load_api_keys()
        invalid_keys = []

        for service, data in config.items():
            if 'api_key' in data:
                if not validate_api_key(service, data['api_key']):
                    print(f"La clave API para {service} no es válida.")
                    invalid_keys.append(service)
            else:
                print(f"No se encontró clave API para {service}.")
                invalid_keys.append(service)

        for service in invalid_keys:
            del config[service]

        if invalid_keys:
            save_api_keys(config)
            print("Se han eliminado las claves API no válidas del archivo KEYS.json.")

        return config

    def setup_translators(self):
        self.translators = {
            'google': GoogleTranslator(),
            'deepl': DeepLTranslator(auth_key=self.config.get('deepl', {}).get('api_key')) if 'deepl' in self.config else None,
            'chatgpt': None
        }
        
    @log_function
    def show_translation_window(self):
        try:
            if not self.text_groups:
                logger.error("No text groups found for translation.")
                messagebox.showerror("Error OCR", "No se encontraron grupos de texto para traducir.")
                return
    
            self.translation_window = tk.Toplevel(self.viewer.root)
            self.translation_window.title(f"Traducción - Página {self.current_page + 1}, Panel {self.current_panel + 1}")
    
            image_frame = ttk.Frame(self.translation_window)
            image_frame.pack(side=tk.LEFT, padx=10, pady=10)
    
            self.panel_photo = ImageTk.PhotoImage(self.panel_image)
            panel_label = ttk.Label(image_frame, image=self.panel_photo)
            panel_label.pack()
    
            text_frame = ttk.Frame(self.translation_window)
            text_frame.pack(side=tk.RIGHT, padx=10, pady=10, fill=tk.BOTH, expand=True)
    
            default_font = tkfont.nametofont("TkDefaultFont")
            bold_font = tkfont.Font(family=default_font.cget("family"), size=default_font.cget("size")*3, weight="bold")
    
            translations = self.load_translations()
    
            self.text_widgets = []
            for group in self.text_groups:
                group_frame = ttk.LabelFrame(text_frame, text=f"Grupo {group['group']}")
                group_frame.pack(fill=tk.X, padx=5, pady=5)
    
                original_text = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                original_text.insert(tk.END, group['text'])
                original_text.pack(padx=5, pady=2)
                original_text.config(height=original_text.count('1.0', tk.END, 'displaylines'))
    
                translation1 = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                translation1.pack(padx=5, pady=2)
    
                translation2 = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                translation2.pack(padx=5, pady=2)
    
                key = f"page_{self.current_page}_panel_{self.current_panel}_group_{group['group']}"
                if key in translations:
                    translation1.insert(tk.END, translations[key].get('translation1', 'Sin traducción'))
                    translation2.insert(tk.END, translations[key].get('translation2', 'Sin traducción'))
                else:
                    translation1.insert(tk.END, 'Sin traducción')
                    translation2.insert(tk.END, 'Sin traducción')
    
                for widget in [translation1, translation2]:
                    widget.config(height=widget.count('1.0', tk.END, 'displaylines'))
    
                self.text_widgets.append((original_text, translation1, translation2))
    
            button_frame = ttk.Frame(self.translation_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
    
            ttk.Button(button_frame, text="Traducir", command=self.translate_texts).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Guardar", command=self.save_translations).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cerrar", command=self.translation_window.destroy).pack(side=tk.RIGHT, padx=5)
        except Exception as e:
            logger.error(f"Error showing translation window: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al mostrar la ventana de traducción: {e}")

    def load_translations(self):
        try:
            with open(f"{self.panel_manager.input_file}.tra", 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            logger.error("Error decoding translation file")
            return {}

    @log_function
    def save_translations(self):
        translations = {}
        for i, (original, trans1, trans2) in enumerate(self.text_widgets):
            key = f"page_{self.current_page}_panel_{self.current_panel}_group_{i+1}"
            translations[key] = {
                'original': original.get('1.0', tk.END).strip(),
                'translation1': trans1.get('1.0', tk.END).strip(),
                'translation2': trans2.get('1.0', tk.END).strip()
            }
        
        try:
            try:
                with open(f"{self.panel_manager.input_file}.tra", 'r', encoding='utf-8') as f:
                    existing_translations = json.load(f)
            except FileNotFoundError:
                existing_translations = {}
    
            existing_translations.update(translations)
    
            with open(f"{self.panel_manager.input_file}.tra", 'w', encoding='utf-8') as f:
                json.dump(existing_translations, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Éxito", "Traducciones guardadas correctamente")
        except Exception as e:
            logger.error(f"Error saving translations: {e}", exc_info=True)
            messagebox.showerror("Error", f"No se pudieron guardar las traducciones: {str(e)}")        
        
class ComicTranslationManager:
    @log_function
    def __init__(self, viewer, panel_manager):
        self.viewer = viewer
        self.panel_manager = panel_manager
        self.config = {}
        self.service_order = []

    @log_function
    def configure_translation_services(self):
        root = tk.Tk()
        app = TranslationConfiguratorApp(root)
        root.mainloop()
        self.config = app.config
        self.service_order = app.service_order

    @log_function
    def start_translation(self, page, panel, image):
        for service in self.service_order:
            config = self.config.get(service, {})
            translator = ConfiguredTranslationManager(service, config)
            text = self.perform_ocr(image)
            if text:
                translation = translator.translate(text, 'auto', 'en')
                if translation:
                    self.show_translation(translation)
                    break

    @log_function
    def perform_ocr(self, image):
        try:
            text = pytesseract.image_to_string(image, lang='eng+spa+deu')
            return text
        except Exception as e:
            logger.error(f"Error performing OCR: {e}", exc_info=True)
            messagebox.showerror("Error OCR", f"Ocurrió un error durante la extracción de texto: {e}")
            return ""

    @log_function
    def show_translation(self, translation):
        self.translation_window = tk.Toplevel(self.viewer.root)
        self.translation_window.title("Translation")
        
        text_widget = tk.Text(self.translation_window)
        text_widget.insert(tk.END, translation)
        text_widget.pack(padx=10, pady=10)

        ttk.Button(self.translation_window, text="Close", command=self.translation_window.destroy).pack(pady=10)

    @log_function
    def translate_with_chatgpt(self, text, source_lang, target_lang):
        if 'chatgpt' not in self.config or 'api_key' not in self.config['chatgpt']:
            api_key = self.request_api_key('chatgpt')
            if not api_key:
                raise ValueError("ChatGPT API key not provided")
            self.config['chatgpt'] = {'api_key': api_key}
            save_api_keys(self.config)
        
        openai.api_key = self.config['chatgpt']['api_key']

    def translate_with_deepl(self, text, source_lang, target_lang):
        if 'deepl' not in self.config or 'api_key' not in self.config['deepl']:
            api_key = self.request_api_key('deepl')
            if not api_key:
                raise ValueError("DeepL API key not provided")
            self.config['deepl'] = {'api_key': api_key}
            save_api_keys(self.config)
            self.translators['deepl'] = DeepLTranslator(auth_key=api_key)

    def request_api_key(self, service):
        return self.viewer.ask_for_api_key(service)

    @log_function
    def show_translation_window(self):
        try:
            if not self.text_groups:
                logger.error("No text groups found for translation.")
                messagebox.showerror("Error OCR", "No se encontraron grupos de texto para traducir.")
                return
    
            self.translation_window = tk.Toplevel(self.viewer.root)
            self.translation_window.title(f"Traducción - Página {self.current_page + 1}, Panel {self.current_panel + 1}")
    
            top_frame = ttk.Frame(self.translation_window)
            top_frame.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)
    
            image_frame = ttk.Frame(top_frame)
            image_frame.pack(side=tk.LEFT, padx=10)
            self.panel_photo = ImageTk.PhotoImage(self.panel_image)
            panel_label = ttk.Label(image_frame, image=self.panel_photo)
            panel_label.pack()
    
            service_frame = ttk.Frame(top_frame)
            service_frame.pack(side=tk.RIGHT, padx=10)
            ttk.Label(service_frame, text="Servicio de traducción:").pack()
            self.service_var = tk.StringVar(value="GoogleTranslate")
            for service in ["GoogleTranslate", "DeepL", "ChatGPT"]:
                ttk.Radiobutton(service_frame, text=service, variable=self.service_var, 
                                value=service, command=self.check_api_key).pack(anchor=tk.W)
    
            text_frame = ttk.Frame(self.translation_window)
            text_frame.pack(side=tk.TOP, padx=10, pady=10, fill=tk.BOTH, expand=True)
    
            default_font = tkfont.nametofont("TkDefaultFont")
            bold_font = tkfont.Font(family=default_font.cget("family"), size=default_font.cget("size")*3, weight="bold")
    
            translations = self.load_translations()
    
            self.text_widgets = []
            for group in self.text_groups:
                group_frame = ttk.LabelFrame(text_frame, text=f"Grupo {group['group']}")
                group_frame.pack(fill=tk.X, padx=5, pady=5)
    
                original_text = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                original_text.insert(tk.END, group['text'])
                original_text.pack(padx=5, pady=2)
                original_text.config(height=original_text.count('1.0', tk.END, 'displaylines'))
    
                translation1 = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                translation1.pack(padx=5, pady=2)
    
                translation2 = tk.Text(group_frame, width=50, font=bold_font, wrap=tk.WORD)
                translation2.pack(padx=5, pady=2)
    
                key = f"page_{self.current_page}_panel_{self.current_panel}_group_{group['group']}"
                if key in translations:
                    translation1.insert(tk.END, translations[key].get('translation1', 'Sin traducción'))
                    translation2.insert(tk.END, translations[key].get('translation2', 'Sin traducción'))
                else:
                    translation1.insert(tk.END, 'Sin traducción')
                    translation2.insert(tk.END, 'Sin traducción')
    
                for widget in [translation1, translation2]:
                    widget.config(height=widget.count('1.0', tk.END, 'displaylines'))
    
                self.text_widgets.append((original_text, translation1, translation2))
    
            button_frame = ttk.Frame(self.translation_window)
            button_frame.pack(fill=tk.X, padx=10, pady=10)
    
            ttk.Button(button_frame, text="Traducir", command=self.translate_texts).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Guardar", command=self.save_translations).pack(side=tk.LEFT, padx=5)
            ttk.Button(button_frame, text="Cerrar", command=self.translation_window.destroy).pack(side=tk.RIGHT, padx=5)
        
        except Exception as e:
            logger.error(f"Error showing translation window: {e}", exc_info=True)
            messagebox.showerror("Error", f"Ocurrió un error al mostrar la ventana de traducción: {e}")

    def check_api_key(self):
        service = self.service_var.get()
        if service != "GoogleTranslate":
            if not self.config.get(service, {}).get('api_key'):
                api_key = simpledialog.askstring(f"{service} API Key", 
                                                 f"No existe el Key para {service}. Ingrese el Key:")
                if api_key:
                    self.config[service] = {'api_key': api_key}
                    self.save_config()
                else:
                    messagebox.showwarning("Advertencia", f"No se ha configurado la clave API para {service}.")
                    self.service_var.set("GoogleTranslate")

    @log_function
    def translate_texts(self):
        service = self.service_var.get()
        if service != "GoogleTranslate" and not self.config.get(service, {}).get('api_key'):
            messagebox.showwarning("Advertencia", f"No se ha configurado la clave API para {service}.")
            return

        if service == "GoogleTranslate":
            translator = self.translators['google']
        elif service == "DeepL":
            translator = self.translators['deepl']
        elif service == "ChatGPT":
            pass

    @log_function
    def load_and_validate_keys(self):
        config = load_api_keys()
        for service, data in config.items():
            if service in ['DeepL', 'ChatGPT'] and 'api_key' in data:
                if not validate_api_key(service, data['api_key']):
                    print(f"La clave API para {service} no es válida.")
                    del config[service]
        return config

    @log_function
    def setup_translators(self):
        self.translators = {
            'GoogleTranslate': self.translator,
            'DeepL': None,
            'ChatGPT': None
        }
        
        if 'DeepL' in self.config and 'api_key' in self.config['DeepL']:
            from deepl import Translator as DeepLTranslator
            self.translators['DeepL'] = DeepLTranslator(auth_key=self.config['DeepL']['api_key'])
        
        if 'ChatGPT' in self.config and 'api_key' in self.config['ChatGPT']:
            import openai
            openai.api_key = self.config['ChatGPT']['api_key']
            self.translators['ChatGPT'] = openai

    @log_function
    def get_current_service(self):
        return self.service_config["service"]

    @log_function
    def get_available_services(self):
        return ["GoogleTranslate", "DeepL", "ChatGPT"]

    @log_function
    def set_service_config(self, service, api_key):
        self.service_config["service"] = service
        self.service_config["api_key"] = api_key

    @log_function
    def translate(self, text, source_lang, target_lang):
        service = self.get_current_service()
        if service == "GoogleTranslate":
            return self.translate_with_google(text, source_lang, target_lang)
        elif service == "DeepL":
            return self.translate_with_deepl(text, source_lang, target_lang)
        elif service == "ChatGPT":
            return self.translate_with_chatgpt(text, source_lang, target_lang)
        else:
            raise ValueError(f"Unsupported translation service: {service}")

    @log_function
    def save_config(self):
        self.config['service_order'] = self.service_order
        save_api_keys(self.config)

def main():
    root = tk.Tk()
    translation_manager = TranslationManager("google", {})
    app = TranslationConfiguratorApp(root, translation_manager)
    root.mainloop()
    return app.translation_manager

def run_configurator():
    root = tk.Tk()
    translation_manager = TranslationManager("google", {})
    app = TranslationConfiguratorApp(root, translation_manager)
    root.mainloop()
    return app.translation_manager

if __name__ == "__main__":
    updated_translation_manager = run_configurator()
