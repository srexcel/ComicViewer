import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from PIL import Image, ImageTk
from translation_manager import TranslationManager
from panel_order_editor import PanelOrderEditor
import logging
import sys
import platform

def setup_logger():
    logging.basicConfig(filename='comic_viewer.log', level=logging.DEBUG,
                        format='%(asctime)s - %(levellevel)s - %(message)s')
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

class PanelEditor:
    def __init__(self, master, panel_manager, current_page):
        self.top = tk.Toplevel(master)
        self.top.title("Agregar/Modificar Paneles")
        self.top.geometry("1400x1050")
        self.panel_manager = panel_manager
        self.current_page = current_page
        self.current_panel = None
        self.panels = self.panel_manager.get_panels(self.current_page)
        self.selected_panel = None
        self.scale_factor = 1.0
        self.viewing_panels = False
        self.translation_manager = TranslationManager(self.top, self)
        self.original_image = None
        self.image = None
        self.photo = None
        self.multiple_selection = []

        self.create_ui()
        self.load_image()

    def create_ui(self):
        self.frame = ttk.Frame(self.top)
        self.frame.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(self.frame)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scrollbar_y = ttk.Scrollbar(self.frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)

        self.scrollbar_x = ttk.Scrollbar(self.top, orient=tk.HORIZONTAL, command=self.canvas.xview)
        self.scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        self.canvas.configure(xscrollcommand=self.scrollbar_x.set, yscrollcommand=self.scrollbar_y.set)

        self.canvas.bind("<ButtonPress-1>", self.on_press)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_release)
        self.canvas.bind("<Configure>", self.on_resize)

        control_frame = ttk.Frame(self.top)
        control_frame.pack(fill=tk.X)

        self.selected_label = ttk.Label(control_frame, text="Panel seleccionado: Ninguno")
        self.selected_label.pack(side=tk.LEFT, padx=5, pady=5)

        button_frame = ttk.Frame(self.top)
        button_frame.pack(fill=tk.X)

        self.save_button = ttk.Button(button_frame, text="Guardar Nuevo Panel", command=self.save_panel)
        self.save_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.delete_button = ttk.Button(button_frame, text="Eliminar Panel Seleccionado", command=self.confirm_delete_panel)
        self.delete_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.prev_button = ttk.Button(button_frame, text="Anterior", command=self.prev_page)
        self.prev_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.next_button = ttk.Button(button_frame, text="Siguiente", command=self.next_page)
        self.next_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.go_to_page_button = ttk.Button(button_frame, text="Ir a página", command=self.go_to_page)
        self.go_to_page_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.clear_selection_button = ttk.Button(button_frame, text="Limpiar selección", command=self.clear_selection)
        self.clear_selection_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.auto_remove_button = ttk.Button(button_frame, text="Auto-eliminar paneles", command=self.auto_remove_panels)
        self.auto_remove_button.pack(side=tk.LEFT, padx=5, pady=5)

        self.reorder_button = ttk.Button(button_frame, text="Reordenar Paneles", command=self.reorder_panels)
        self.reorder_button.pack(side=tk.LEFT, padx=5, pady=5)

    def load_image(self):
        image_path = self.panel_manager.get_page_path(self.current_page)
        self.original_image = Image.open(image_path)
        self.panels = self.panel_manager.get_panels(self.current_page)
        self.multiple_selection = []
        self.fit_image_to_canvas()

    def fit_image_to_canvas(self):
        if self.original_image:
            canvas_width = self.canvas.winfo_width()
            canvas_height = self.canvas.winfo_height()

            if canvas_width <= 0 or canvas_height <= 0:
                logger.error("Invalid canvas dimensions: width or height is <= 0.")
                return
            
            img_ratio = self.original_image.width / self.original_image.height
            canvas_ratio = canvas_width / canvas_height

            if img_ratio > canvas_ratio:
                width = canvas_width
                height = int(width / img_ratio)
            else:
                height = canvas_height
                width = int(height * img_ratio)

            if width <= 0 or height <= 0:
                logger.error(f"Invalid calculated dimensions: width={width}, height={height}.")
                return

            self.scale_factor = width / self.original_image.width

            self.image = self.original_image.copy()
            self.image = self.image.resize((width, height), Image.LANCZOS)
            self.photo = ImageTk.PhotoImage(self.image)

            self.canvas.delete("all")
            self.canvas.create_image(canvas_width/2, canvas_height/2, image=self.photo, anchor='center')
            self.canvas.config(scrollregion=self.canvas.bbox(tk.ALL))

            self.draw_panels()

    def draw_panels(self):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.image.width
        image_height = self.image.height
        
        offset_x = (canvas_width - image_width) / 2
        offset_y = (canvas_height - image_height) / 2
        
        for i, (x1, y1, x2, y2) in enumerate(self.panels):
            scaled_x1, scaled_y1 = x1 * self.scale_factor, y1 * self.scale_factor
            scaled_x2, scaled_y2 = x2 * self.scale_factor, y2 * self.scale_factor
            
            self.canvas.create_rectangle(scaled_x1 + offset_x, scaled_y1 + offset_y, 
                                         scaled_x2 + offset_x, scaled_y2 + offset_y, 
                                         outline="red", width=2, tags=f"panel{i}")
            self.canvas.create_text((scaled_x1 + scaled_x2) / 2 + offset_x, 
                                    (scaled_y1 + scaled_y2) / 2 + offset_y, 
                                    text=str(i+1), fill="yellow", font=("Arial", 20, "bold"),
                                    tags=f"panel{i}")
            self.canvas.tag_bind(f"panel{i}", "<Button-1>", lambda e, i=i: self.select_panel(i))
        
        for i, (x1, y1, x2, y2) in enumerate(self.multiple_selection):
            scaled_x1, scaled_y1 = x1 * self.scale_factor, y1 * self.scale_factor
            scaled_x2, scaled_y2 = x2 * self.scale_factor, y2 * self.scale_factor
            
            self.canvas.create_rectangle(scaled_x1 + offset_x, scaled_y1 + offset_y, 
                                         scaled_x2 + offset_x, scaled_y2 + offset_y, 
                                         outline="blue", width=2, tags="new_panel")

    def on_press(self, event):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.image.width
        image_height = self.image.height
        
        offset_x = (canvas_width - image_width) / 2
        offset_y = (canvas_height - image_height) / 2
        
        self.start_x = (event.x - offset_x) / self.scale_factor
        self.start_y = (event.y - offset_y) / self.scale_factor

    def on_drag(self, event):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.image.width
        image_height = self.image.height
        
        offset_x = (canvas_width - image_width) / 2
        offset_y = (canvas_height - image_height) / 2
        
        cur_x = (event.x - offset_x) / self.scale_factor
        cur_y = (event.y - offset_y) / self.scale_factor

        self.canvas.delete("new_panel")
        scaled_x1 = self.start_x * self.scale_factor + offset_x
        scaled_y1 = self.start_y * self.scale_factor + offset_y
        scaled_x2 = cur_x * self.scale_factor + offset_x
        scaled_y2 = cur_y * self.scale_factor + offset_y
        self.canvas.create_rectangle(scaled_x1, scaled_y1, scaled_x2, scaled_y2, 
                                     outline="blue", width=2, tags="new_panel")

    def on_release(self, event):
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.image.width
        image_height = self.image.height
        
        offset_x = (canvas_width - image_width) / 2
        offset_y = (canvas_height - image_height) / 2
        
        self.end_x = (event.x - offset_x) / self.scale_factor
        self.end_y = (event.y - offset_y) / self.scale_factor

        x1, y1 = min(self.start_x, self.end_x), min(self.start_y, self.end_y)
        x2, y2 = max(self.start_x, self.end_x), max(self.start_y, self.end_y)
        
        new_panel = (int(x1), int(y1), int(x2), int(y2))
        self.multiple_selection.append(new_panel)
        self.fit_image_to_canvas()

    def select_panel(self, index):
        self.selected_panel = index
        self.canvas.delete("selected")
        x1, y1, x2, y2 = self.panels[index]
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        image_width = self.image.width
        image_height = self.image.height
        
        offset_x = (canvas_width - image_width) / 2
        offset_y = (canvas_height - image_height) / 2
        
        scaled_x1, scaled_y1 = x1 * self.scale_factor, y1 * self.scale_factor
        scaled_x2, scaled_y2 = x2 * self.scale_factor, y2 * self.scale_factor
        self.canvas.create_rectangle(scaled_x1 + offset_x, scaled_y1 + offset_y, 
                                     scaled_x2 + offset_x, scaled_y2 + offset_y, 
                                     outline= "green", width=3, tags="selected")
        self.selected_label.config(text=f"Panel seleccionado: {index + 1}")

    def save_panel(self):
        self.panels.extend(self.multiple_selection)
        self.panel_manager.set_panels(self.current_page, self.panels)
        self.multiple_selection = []
        self.fit_image_to_canvas()

    def confirm_delete_panel(self):
        if self.selected_panel is not None:
            result = messagebox.askyesno("Confirmar eliminación", 
                                         f"¿Está seguro de que desea eliminar el panel {self.selected_panel + 1}?")
            if result:
                self.delete_panel()
        else:
            messagebox.showwarning("No hay panel seleccionado", 
                                   "Por favor, seleccione un panel antes de intentar eliminarlo.")

    def delete_panel(self):
        if self.selected_panel is not None:
            del self.panels[self.selected_panel]
            self.selected_panel = None
            self.panel_manager.set_panels(self.current_page, self.panels)
            self.fit_image_to_canvas()
            self.selected_label.config(text="Panel seleccionado: Ninguno")

    def prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self.load_image()

    def next_page(self):
        if self.current_page < self.panel_manager.get_num_pages() - 1:
            self.current_page += 1
            self.load_image()

    def go_to_page(self):
        new_page = simpledialog.askinteger("Ir a página", "Ingrese el número de página:", 
                                           minvalue=1, maxvalue=self.panel_manager.get_num_pages())
        if new_page:
            self.current_page = new_page - 1
            self.load_image()

    def clear_selection(self):
        self.multiple_selection = []
        self.fit_image_to_canvas()

    def auto_remove_panels(self):
        new_panels = []
        for i, panel in enumerate(self.panels):
            is_contained = False
            for j, other_panel in enumerate(self.panels):
                if i != j and self.is_panel_contained(panel, other_panel, threshold=0.8):
                    is_contained = True
                    break
            if not is_contained:
                new_panels.append(panel)
        
        removed_count = len(self.panels) - len(new_panels)
        self.panels = new_panels
        self.panel_manager.set_panels(self.current_page, self.panels)
        self.fit_image_to_canvas()
        messagebox.showinfo("Auto-eliminación", f"Se han eliminado {removed_count} paneles.")

    def is_panel_contained(self, panel1, panel2, threshold=0.8):
        x1, y1, x2, y2 = panel1
        X1, Y1, X2, Y2 = panel2
        
        intersection_area = max(0, min(x2, X2) - max(x1, X1)) * max(0, min(y2, Y2) - max(y1, Y1))
        panel1_area = (x2 - x1) * (y2 - y1)
        
        return intersection_area / panel1_area > threshold

    @log_function  
    def reorder_panels(self):
        logger.info(f"Reordering panels for page {self.current_page + 1}")
        panels = self.panel_manager.get_panels(self.current_page)
        if panels:
            if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de la página actual?"):
                order_editor = PanelOrderEditor(self.top, self.panel_manager, self.current_page, self.save_new_order, self._reorder_remaining_pages)
                self.top.wait_window(order_editor.top)
            else:
                if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de todas las hojas remanentes?"):
                    self._reorder_remaining_pages(self.current_page)
                else:
                    if messagebox.askyesno("Reordenar paneles", "¿Desea reordenar los paneles de páginas específicas?"):
                        self._reorder_specific_pages()
                    else:
                        logger.info("Panel reordering cancelled by user")
        else:
            messagebox.showinfo("Sin paneles", f"No hay paneles para reordenar en la página {self.current_page + 1}")

    @log_function
    def save_new_order(self, page, new_order):
        logger.info(f"Saving new panel order for page {page + 1}")
        self.panel_manager.set_panels(page, new_order)
        self.load_image()

    @log_function
    def _reorder_remaining_pages(self, start_page):
        num_pages = self.panel_manager.get_num_pages()
        for page in range(start_page, num_pages):
            panels = self.panel_manager.get_panels(page)
            if panels:
                panels.sort(key=lambda p: (p[1], p[0]))  # Ordenar por coordenadas (y, x)
                self.panel_manager.set_panels(page, panels)
                logger.info(f"Reordenados paneles en página {page + 1}")
        self.load_image()
        messagebox.showinfo("Reordenar", "Se han reordenado todas las hojas remanentes automáticamente.")

    @log_function
    def _reorder_specific_pages(self):
        page_input = simpledialog.askstring("Reordenar paneles", 
                                            "Ingrese las páginas a reordenar (ejemplo: 1,3,4-8,10,11-12,15):")
        if page_input:
            pages_to_reorder = self._parse_page_input(page_input)
            for page in pages_to_reorder:
                self._reorder_single_page(page - 1)  # Restamos 1 porque internamente las páginas empiezan en 0
            messagebox.showinfo("Reordenamiento completado", f"Se han reordenado los paneles de las siguientes páginas: {page_input}")
        else:
            logger.info("User cancelled specific page reordering")

    @log_function
    def _reorder_single_page(self, page):
        panels = self.panel_manager.get_panels(page)
        if panels:
            order_editor = PanelOrderEditor(self.top, self.panel_manager, page, self.save_new_order, self._reorder_remaining_pages)
            self.top.wait_window(order_editor.top)

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
    def on_resize(self, event):
        self.fit_image_to_canvas()
