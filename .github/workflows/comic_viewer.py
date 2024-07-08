import os
from tkinter import Tk, filedialog, Button, Canvas, BOTH, LEFT, RIGHT, Y, VERTICAL, messagebox, Frame, Scrollbar, Label, X
from panel_manager import PanelManager
from panel_editor import PanelEditor
from panel_order_editor import PanelOrderEditor
from panel_recalculation import recalcular_paneles
from PIL import Image, ImageTk
from utils import ensure_directory_exists

class ComicViewer:
    def __init__(self, root):
        self.root = root
        self.root.title("Comic Viewer")
        self.create_ui()
        self.current_page = 0
        self.current_panel = 0
        self.panels_to_show = 1
        self.viewing_panels = False
        self.extract_dir = 'extracted_comic'
        ensure_directory_exists(self.extract_dir)
        self.panel_manager = None

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
        self.prev_button = Button(self.button_frame, text="Anterior", command=self.prev_item)
        self.prev_button.pack(fill=X)
        self.next_button = Button(self.button_frame, text="Siguiente", command=self.next_item)
        self.next_button.pack(fill=X)
        self.toggle_button = Button(self.button_frame, text="Ver Paneles", command=self.toggle_panels)
        self.toggle_button.pack(fill=X)
        self.correct_button = Button(self.button_frame, text="Agregar/Corregir Paneles", command=self.correct_panels)
        self.correct_button.pack(fill=X)
        self.delete_button = Button(self.button_frame, text="Borrar Panel", command=self.delete_current_panel)
        self.delete_button.pack(fill=X)
        self.save_button = Button(self.button_frame, text="Guardar", command=self.save_corrections)
        self.save_button.pack(fill=X)
        self.reload_button = Button(self.button_frame, text="Recargar guía", command=self.reload_gui)
        self.reload_button.pack(fill=X)
        self.reorder_button = Button(self.button_frame, text="Reordenar Paneles", command=self.reorder_panels)
        self.reorder_button.pack(fill=X)
        self.refresh_panels_button = Button(self.button_frame, text="Recargar Paneles", command=self.refresh_panels)
        self.refresh_panels_button.pack(fill=X)
        self.recalculate_panels_button = Button(self.button_frame, text="Recalculo de paneles", command=self.recalculate_panels)
        self.recalculate_panels_button.pack(fill=X)

        self.info_label = Label(self.button_frame, text="", anchor="e", justify=RIGHT)
        self.info_label.pack(fill=X)

        self.increase_panels_button = Button(self.button_frame, text="Más Paneles", command=self.increase_panels)
        self.increase_panels_button.pack(fill=X)
        self.decrease_panels_button = Button(self.button_frame, text="Menos Paneles", command=self.decrease_panels)
        self.decrease_panels_button.pack(fill=X)

    def load_comic(self):
        self.input_file = filedialog.askopenfilename(title="Selecciona el archivo de cómic", filetypes=[("Comic files", "*.cbr *.cbz *.rar *.zip")])

        if not self.input_file:
            print("No se seleccionó ningún archivo.")
            return

        try:
            self.panel_manager = PanelManager(self.input_file)
            self.image_files = self.panel_manager.get_image_files()
            self.current_page = 0
            self.current_panel = 0
            self.viewing_panels = False
            self.show_current_page()
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el cómic: {str(e)}")
            print(f"Error al cargar el cómic: {str(e)}")

    def show_current_page(self):
        print(f"Mostrando página actual: {self.current_page}")
        page_path = self.panel_manager.extract_page(self.current_page)
        if page_path:
            try:
                image = Image.open(page_path)
                self.tkimage = self.resize_image_to_canvas(image)
                self.canvas.delete("all")  # Clear the canvas completely
                self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, anchor='center', image=self.tkimage)
                self.panel_images = self.panel_manager.get_panels(self.current_page)
                self.remove_zero_size_panels()  # Remover paneles de tamaño cero
                if not self.viewing_panels:
                    self.draw_panels()
                self.update_info_label()
                print("Página actual mostrada correctamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo mostrar la página: {str(e)}")
                print(f"Error al mostrar la página: {str(e)}")

    def resize_image_to_canvas(self, image):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        if canvas_width == 0 or canvas_height == 0:
            print("Canvas size is zero. Returning original image.")
            return ImageTk.PhotoImage(image)

        image_ratio = image.width / image.height
        canvas_ratio = canvas_width / canvas_height

        if image_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / image_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * image_ratio)

        self.scale_x = image.width / new_width
        self.scale_y = image.height / new_height

        resized_image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        tkimage = ImageTk.PhotoImage(resized_image)

        print(f"Resizing image to: {new_width}x{new_height}")
        return tkimage

    def draw_panels(self):
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            scaled_coords = self.scale_coords(x1, y1, x2, y2, invert=True)
            rect = self.canvas.create_rectangle(*scaled_coords, outline="red", width=5, tags=("panel", str(i)))
            self.canvas.create_text(scaled_coords[0] + 5, scaled_coords[1] + 5, text=str(i + 1), anchor="nw", fill="white", tags=("panel", str(i)))
            self.canvas.tag_bind(rect, "<Button-1>", lambda event, idx=i: self.select_panel(event, idx))
            self.canvas.tag_bind(rect, "<Button-3>", lambda event, idx=i: self.delete_panel(event, idx))
        print("Paneles dibujados:", self.panel_images)

    def scale_coords(self, x1, y1, x2, y2, invert=False):
        if invert:
            return x1 / self.scale_x, y1 / self.scale_y, x2 / self.scale_x, y2 / self.scale_y
        else:
            return x1 * self.scale_x, y1 * self.scale_y, x2 * self.scale_x, y2 * self.scale_y

    def show_current_panel(self):
        print(f"Mostrando panel actual: {self.current_panel}")
        if self.current_panel < len(self.panel_images):
            page_path = self.panel_manager.extract_page(self.current_page)
            if page_path:
                try:
                    x1, y1, x2, y2 = self.panel_images[self.current_panel]
                    panel_img = Image.open(page_path).crop((x1, y1, x2, y2))
                    self.tkimage = self.resize_image_to_canvas(panel_img)
                    self.canvas.delete("all")  # Clear the canvas completely
                    self.canvas.create_image(self.canvas.winfo_width() // 2, self.canvas.winfo_height() // 2, anchor='center', image=self.tkimage)
                    self.update_info_label()
                    print("Panel actual mostrado correctamente.")
                except Exception as e:
                    messagebox.showerror("Error", f"No se pudo mostrar el panel: {str(e)}")
                    print(f"Error al mostrar el panel: {str(e)}")
        else:
            messagebox.showerror("Error", "No hay más paneles para mostrar.")
            print("Error: No hay más paneles para mostrar.")

    def next_item(self):
        print("Siguiente ítem.")
        if self.viewing_panels:
            if self.current_panel < len(self.panel_images) - 1:
                self.current_panel += 1
                self.show_current_panel()
            else:
                self.next_page()
        else:
            self.next_page()

    def prev_item(self):
        print("Ítem anterior.")
        if self.viewing_panels:
            if self.current_panel > 0:
                self.current_panel -= 1
                self.show_current_panel()
            else:
                self.prev_page()
        else:
            self.prev_page()

    def next_page(self):
        print("Siguiente página.")
        if self.current_page < len(self.image_files) - 1:
            self.current_page += 1
            self.current_panel = 0
            self.reload_gui()  # Recargar la guía al cambiar de página
            self.show_current_page() if not self.viewing_panels else self.show_current_panel()

    def prev_page(self):
        print("Página anterior.")
        if self.current_page > 0:
            self.current_page -= 1
            self.current_panel = 0
            self.reload_gui()  # Recargar la guía al cambiar de página
            self.show_current_page() if not self.viewing_panels else self.show_current_panel()

    def toggle_panels(self):
        self.viewing_panels = not self.viewing_panels
        print(f"Modo de visualización cambiado a {'paneles' if self.viewing_panels else 'página completa'}.")
        if self.viewing_panels:
            self.show_current_panel()
        else:
            self.show_current_page()

    def correct_panels(self):
        editor = PanelEditor(self.root, self.panel_manager, self.current_page)
        self.root.wait_window(editor.top)
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.draw_panels()
        self.update_info_label()
        print("Modo de corrección de paneles activado.")

    def delete_current_panel(self):
        print(f"Eliminando panel actual: {self.current_panel}.")
        if self.current_panel < len(self.panel_images):
            self.panel_manager.delete_panel(self.current_page, self.current_panel)
            self.panel_manager.save_gui_file()
            self.reload_gui()
            print(f"Panel actual {self.current_panel} eliminado.")

    def save_corrections(self):
        self.panel_manager.save_gui_file()
        print("Correcciones guardadas:", self.panel_manager.panel_corrections)

    def reload_gui(self):
        print("Recargando GUI.")
        self.panel_manager = PanelManager(self.input_file)  # Recargar el archivo .gui
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.show_current_page()
        print("GUI recargado.")

    def refresh_panels(self):
        print("Recargando paneles desde el archivo .gui.")
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.draw_panels()
        self.update_info_label()
        print("Paneles recargados.")
        if self.viewing_panels and self.current_panel < len(self.panel_images):
            x1, y1, x2, y2 = self.panel_images[self.current_panel]
            self.adjust_window_to_panel(x1, y1, x2, y2)

    def update_info_label(self):
        info_text = f"Modo: {'Paneles' if self.viewing_panels else 'Página completa'}\n"
        info_text += f"Página: {self.current_page + 1}\n"
        if self.viewing_panels:
            info_text += f"Panel: {self.current_panel + 1} de {len(self.panel_images)}\n"
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            info_text += f"Panel {i + 1}: ({x1}, {y1}), ({x2}, {y2})\n"
        self.info_label.config(text=info_text)
        print("Etiqueta de información actualizada.")

    def select_panel(self, event, idx):
        self.current_panel = idx
        x1, y1, x2, y2 = self.panel_images[idx]
        print(f"Panel {idx} seleccionado: ({x1}, {y1}, {x2}, {y2})")

    def remove_zero_size_panels(self):
        print("Eliminando paneles de tamaño cero.")
        self.panel_images = [(x1, y1, x2, y2) for x1, y1, x2, y2 in self.panel_images if (x2 - x1) > 0 and (y2 - y1) > 0]
        self.panel_manager.panel_corrections[self.current_page] = self.panel_images
        self.panel_manager.save_gui_file()
        print("Paneles de tamaño cero eliminados.")

    def adjust_window_to_panel(self, x1, y1, x2, y2):
        panel_width = x2 - x1
        panel_height = y2 - y1
        self.root.geometry(f"{panel_width}x{panel_height}")

    def reorder_panels(self):
        print("Reordenando paneles.")
        order_editor = PanelOrderEditor(self.root, self.panel_manager, self.current_page, self.save_new_order)
        self.root.wait_window(order_editor.top)
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.draw_panels()
        self.update_info_label()
        print("Paneles reordenados.")

    def save_new_order(self, new_order):
        self.panel_images = [self.panel_images[i] for i in new_order]
        self.panel_manager.panel_corrections[self.current_page] = self.panel_images
        self.panel_manager.save_gui_file()
        print("Nuevo orden de paneles guardado.")

    def recalculate_panels(self):
        print("Recalculando paneles.")
        page_path = self.panel_manager.extract_page(self.current_page)
        new_panels = recalcular_paneles(page_path)
        self.panel_manager.panel_corrections[self.current_page] = new_panels
        self.panel_manager.save_gui_file()
        self.refresh_panels()
        print("Paneles recalculados:", new_panels)

    def increase_panels(self):
        self.panels_to_show += 1
        self.refresh_panels()

    def decrease_panels(self):
        if self.panels_to_show > 1:
            self.panels_to_show -= 1
        self.refresh_panels()

