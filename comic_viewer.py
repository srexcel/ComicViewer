import os
from tkinter import Tk, filedialog, Button, Canvas, BOTH, LEFT, RIGHT, Y, VERTICAL, Frame, Scrollbar, Label, X, ALL, messagebox
from panel_manager import PanelManager
from panel_editor import PanelEditor
from panel_order_editor import PanelOrderEditor
from panel_recalculation import recalcular_paneles
from PIL import Image, ImageTk, UnidentifiedImageError
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
        self.panel_images = []
        self.current_image = None
        self.canvas.bind('<Configure>', self.on_resize)

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
        self.zoom_in_button = Button(self.button_frame, text="Aumentar Paneles", command=self.increase_panels)
        self.zoom_in_button.pack(fill=X)
        self.zoom_out_button = Button(self.button_frame, text="Reducir Paneles", command=self.decrease_panels)
        self.zoom_out_button.pack(fill=X)
        self.recalc_button = Button(self.button_frame, text="Recalcular Paneles", command=self.recalculate_panels)
        self.recalc_button.pack(fill=X)
        self.reorder_button = Button(self.button_frame, text="Reordenar Paneles", command=self.reorder_panels)
        self.reorder_button.pack(fill=X)
        self.remove_zero_button = Button(self.button_frame, text="Eliminar Paneles de Tamaño Cero", command=self.remove_zero_size_panels)
        self.remove_zero_button.pack(fill=X)
        self.delete_panel_button = Button(self.button_frame, text="Borrar Panel", command=self.delete_current_panel)
        self.delete_panel_button.pack(fill=X)
        self.add_panel_button = Button(self.button_frame, text="Agregar/Modificar Panel", command=self.add_modify_panel)
        self.add_panel_button.pack(fill=X)
        self.fit_image_button = Button(self.button_frame, text="Ajustar Imagen", command=self.fit_image)
        self.fit_image_button.pack(fill=X)
        self.info_label = Label(self.button_frame, text="", anchor='w')
        self.info_label.pack(fill=X)

    def on_resize(self, event):
        if self.panel_manager:
            if self.viewing_panels:
                self.draw_panels()
            else:
                self.fit_image()

    def load_comic(self):
        file_path = filedialog.askopenfilename(filetypes=[("Comic files", "*.cbz *.cbr")])
        if file_path:
            self.extract_comic(file_path)
            self.panel_manager = PanelManager(file_path)
            self.panel_manager.load_gui_file()
            self.show_page(0)

    def extract_comic(self, file_path):
        print(f"Extrayendo cómic desde {file_path}")
        # Implementación de la extracción de archivos CBZ y CBR

    def show_page(self, page_index):
        if self.panel_manager:
            self.current_page = page_index
            self.viewing_panels = False
            self.panel_images = self.panel_manager.get_panels(page_index)
            self.update_info_label()
            try:
                self.display_image(self.panel_manager.get_page_path(page_index))
            except ValueError as e:
                messagebox.showerror("Error", str(e))

    def display_image(self, image_path):
        try:
            self.current_image = Image.open(image_path)
            self.fit_image()
        except UnidentifiedImageError:
            print(f"Error: no se pudo identificar el archivo de imagen '{image_path}'.")

    def fit_image(self):
        if self.current_image:
            img = self.current_image.copy()
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img.thumbnail((canvas_width, canvas_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image((canvas_width - img.width) // 2, (canvas_height - img.height) // 2, image=self.photo, anchor='nw')
            self.canvas.config(scrollregion=self.canvas.bbox(ALL))

    def next_item(self):
        if self.viewing_panels:
            self.next_panel()
        else:
            self.next_page()

    def prev_item(self):
        if self.viewing_panels:
            self.prev_panel()
        else:
            self.prev_page()

    def next_page(self):
        if self.current_page < self.panel_manager.get_num_pages() - 1:
            self.current_page += 1
            self.show_page(self.current_page)

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.show_page(self.current_page)

    def toggle_panels(self):
        self.viewing_panels = not self.viewing_panels
        if self.viewing_panels:
            self.show_panels()
        else:
            self.show_page(self.current_page)

    def show_panels(self):
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.current_panel = 0
        if self.panel_images:  # Verificar si hay paneles disponibles
            self.display_panel()

    def next_panel(self):
        if self.current_panel < len(self.panel_images) - 1:
            self.current_panel += 1
            self.display_panel()

    def prev_panel(self):
        if self.current_panel > 0:
            self.current_panel -= 1
            self.display_panel()

    def display_panel(self):
        if self.panel_images:
            panel = self.panel_images[self.current_panel]
            x1, y1, x2, y2 = panel
            img = self.current_image.crop((x1, y1, x2, y2))
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()
            img.thumbnail((canvas_width, canvas_height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(img)
            self.canvas.create_image((canvas_width - img.width) // 2, (canvas_height - img.height) // 2, image=self.photo, anchor='nw')
            self.canvas.config(scrollregion=self.canvas.bbox(ALL))
            self.update_info_label()

    def update_info_label(self):
        if self.panel_manager:
            self.info_label.config(text=f"Página: {self.current_page + 1} de {self.panel_manager.get_num_pages()} | Panel: {self.current_panel + 1} de {len(self.panel_images)}")

    def draw_panels(self):
        self.canvas.delete('panel')
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            rect = self.canvas.create_rectangle(x1, y1, x2, y2, outline='red', width=5, tags='panel')
            self.canvas.create_text(x2 - 10, y1 + 10, text=str(i + 1), fill='white', anchor='ne', tags='panel')

    def remove_zero_size_panels(self):
        print("Eliminando paneles de tamaño cero.")
        self.panel_images = [(x1, y1, x2, y2) for x1, y1, x2, y2 in self.panel_images if (x2 - x1) > 0 and (y2 - y1) > 0]
        self.panel_manager.panel_corrections[self.current_page] = self.panel_images
        self.panel_manager.save_gui_file()
        print("Paneles de tamaño cero eliminados.")

    def delete_current_panel(self):
        if self.panel_images:
            del self.panel_images[self.current_panel]
            self.panel_manager.panel_corrections[self.current_page] = self.panel_images
            self.panel_manager.save_gui_file()
            if self.current_panel >= len(self.panel_images):
                self.current_panel = len(self.panel_images) - 1
            if self.panel_images:
                self.display_panel()
            else:
                self.show_page(self.current_page)

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
        reordered_panels = [self.panel_images[i] for i in new_order]
        self.panel_manager.panel_corrections[self.current_page] = reordered_panels
        self.panel_manager.save_gui_file()
        self.panel_images = reordered_panels
        print("Nuevo orden de paneles guardado.")

    def recalculate_panels(self):
        print("Recalculando paneles.")
        page_path = self.panel_manager.extract_page(self.current_page)
        new_panels = recalcular_paneles(page_path)
        self.panel_manager.panel_corrections[self.current_page] = new_panels
        self.panel_manager.save_gui_file()
        self.refresh_panels()
        print("Paneles recalculados:", new_panels)

    def refresh_panels(self):
        if self.viewing_panels:
            self.show_panels()
        else:
            self.show_page(self.current_page)

    def increase_panels(self):
        self.panels_to_show += 1
        self.refresh_panels()

    def decrease_panels(self):
        if self.panels_to_show > 1:
            self.panels_to_show -= 1
        self.refresh_panels()

    def add_modify_panel(self):
        if self.panel_manager:
            panel_editor = PanelEditor(self.root, self.panel_manager, self.current_page)
            self.root.wait_window(panel_editor.top)
            self.panel_images = self.panel_manager.get_panels(self.current_page)
            self.draw_panels()
            self.update_info_label()
            print("Paneles agregados/modificados.")

if __name__ == "__main__":
    root = Tk()
    viewer = ComicViewer(root)
    root.geometry("1400x1000")
    root.mainloop()
