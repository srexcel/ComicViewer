import tkinter as tk
from tkinter import simpledialog, messagebox, Listbox, MULTIPLE, Scrollbar, RIGHT, LEFT, BOTH, END, Toplevel, Button, Label, Entry
import json
import logging
from googletrans import Translator as GoogleTranslator
from deepl import Translator as DeepLTranslator
import openai

def setup_logger():
    logging.basicConfig(filename='translation_configurator.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger('TranslationConfigurator')
    logger.info("Translation Configurator started")
    return logger

logger = setup_logger()

def load_api_keys():
    try:
        with open('api_keys.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

def save_api_keys(api_keys):
    with open('api_keys.json', 'w') as f:
        json.dump(api_keys, f)

def validate_api_key(service, api_key):
    # Add your API key validation logic here if needed
    return True
class TranslationManager:
    def __init__(self, service, config):
        self.service = service
        self.config = config

        if service == "google":
            self.translator = GoogleTranslator()
        elif service == "deepl":
            self.translator = DeepLTranslator(auth_key=config.get('deepl', {}).get('api_key'))
        elif service == "chatgpt":
            openai.api_key = config.get('chatgpt', {}).get('api_key')

        else:
            raise ValueError("Unsupported translation service")



    def translate(self, text, source_lang, target_lang):
        if self.service == "google":
            return self.translate_with_google(text, source_lang, target_lang)
        elif self.service == "deepl":
            return self.translate_with_deepl(text, source_lang, target_lang)
        elif self.service == "chatgpt":
            return self.translate_with_chatgpt(text, source_lang, target_lang)
        elif self.service == "claude":
            return self.translate_with_claude(text, source_lang, target_lang)
        else:
            return None

    def translate_with_google(self, text, source_lang, target_lang):
        try:
            translation = self.translator.translate(text, src=source_lang, dest=target_lang)
            return translation.text
        except Exception as e:
            logger.error(f"Google Translate error: {e}", exc_info=True)
            return None

    def translate_with_deepl(self, text, source_lang, target_lang):
        try:
            translation = self.translator.translate_text(text, source_lang=source_lang, target_lang=target_lang)
            return translation.text
        except Exception as e:
            logger.error(f"DeepL Translate error: {e}", exc_info=True)
            return None

    def translate_with_chatgpt(self, text, source_lang, target_lang):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": f"Translate the following text from {source_lang} to {target_lang}."},
                    {"role": "user", "content": text}
                ]
            )
            return response.choices[0].message['content'].strip()
        except Exception as e:
            logger.error(f"ChatGPT Translate error: {e}", exc_info=True)
            return None

    def translate_with_claude(self, text, source_lang, target_lang):
        try:
            prompt = f"Translate the following text from {source_lang} to {target_lang}: {text}"
            response = self.claude_client.completions.create(
                model="claude-2",
                prompt=prompt,
                max_tokens_to_sample=300
            )
            return response.completion.strip()
        except Exception as e:
            logger.error(f"Claude Translate error: {e}", exc_info=True)
            return None

    def update_config(self, service, api_key):
        self.config[service] = {'api_key': api_key}

class TranslationConfiguratorApp:
    def __init__(self, root, translation_manager):
        self.root = root
        self.translation_manager = translation_manager
        self.root.title("Translation Configurator")
        self.config = load_api_keys()
        self.service_order = []

        self.services = {
            "Google Translate": "google",
            "DeepL": "deepl",
            "ChatGPT": "chatgpt",
            "Claude": "claude"
        }

        self.create_widgets()
    def close_window(self):
        self.root.destroy()
        
    def create_widgets(self):
        Label(self.root, text="Configuración de API Keys").pack(pady=10)
        close_button = Button(self.root, text="Cerrar", command=self.close_window)
        close_button.pack(pady=5)

        self.entries = {}
        for service in ["deepl", "chatgpt"]:
            Label(self.root, text=f"{service.capitalize()} API Key:").pack()
            self.entries[service] = Entry(self.root, show="*")
            self.entries[service].pack()

        save_button = Button(self.root, text="Guardar", command=self.save_config)
        save_button.pack(pady=5)

        close_button = Button(self.root, text="Cerrar", command=self.close_window)
        close_button.pack(pady=5)

        show_keys_button = Button(self.root, text="Mostrar API Keys", command=self.show_api_keys)
        show_keys_button.pack(pady=5)

        disable_service_button = Button(self.root, text="Deshabilitar Servicio", command=self.disable_service)
        disable_service_button.pack(pady=5)

        default_service_button = Button(self.root, text="Servicio Predeterminado", command=self.set_default_service)
        default_service_button.pack(pady=5)

        configure_languages_button = Button(self.root, text="Configurar Idiomas", command=self.configure_languages)
        configure_languages_button.pack(pady=5)

    def save_config(self):
        for service in self.entries:
            self.config[service] = {"api_key": self.entries[service].get()}
        self.translation_manager.config.update(self.config)
        save_api_keys(self.config)
        messagebox.showinfo("Configuración Guardada", "Las configuraciones de API Keys se han guardado correctamente.")

    def close_window(self):
        self.root.destroy()

    def show_api_keys(self):
        api_keys = {service: self.config.get(service, {}).get('api_key', 'Not Set') for service in self.services.values()}
        api_keys_message = "\n".join([f"{service}: {key}" for service, key in api_keys.items()])
        messagebox.showinfo("API Keys", api_keys_message)

    def disable_service(self):
        disabled_service = simpledialog.askstring("Disable Service", "Enter the service to disable (google, deepl, chatgpt, claude):")
        if disabled_service in self.config:
            del self.config[disabled_service]
            save_api_keys(self.config)
            messagebox.showinfo("Info", f"{disabled_service.capitalize()} service disabled.")
        else:
            messagebox.showerror("Error", f"Service {disabled_service} not found in configuration.")

    def set_default_service(self):
        default_service = simpledialog.askstring("Default Service", "Enter the default service (google, deepl, chatgpt, claude):")
        if default_service in self.services.values():
            self.translation_manager.service = default_service
            messagebox.showinfo("Info", f"Default service set to {default_service}.")
        else:
            messagebox.showerror("Error", f"Service {default_service} not found.")

    def configure_languages(self):
        original_language = simpledialog.askstring("Original Language", "Enter the original language (e.g., en for English):")
        language_2 = simpledialog.askstring("Second Language", "Enter the second language (e.g., es for Spanish):")
        language_3 = simpledialog.askstring("Third Language", "Enter the third language (optional):")

        self.translation_manager.config['languages'] = {
            'original': original_language,
            'language_2': language_2,
            'language_3': language_3
        }
        messagebox.showinfo("Info", "Language configuration saved successfully!")
