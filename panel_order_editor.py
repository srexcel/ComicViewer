import tkinter as tk
from tkinter import Toplevel, Canvas, Button, Scrollbar, messagebox
from PIL import Image, ImageTk
import math
import logging
import sys
import platform

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

class PanelOrderEditor:
    def __init__(self, master, panel_manager, page, save_callback, reorder_all_callback):
        self.top = Toplevel(master)
        self.top.title(f"Reordenar Paneles - Página {page + 1}")
        self.top.geometry("1200x750")
        self.panel_manager = panel_manager
        self.page = page
        self.save_callback = save_callback
        self.reorder_all_callback = reorder_all_callback
        self.selected_index = None
        self.panel_images = self.panel_manager.get_panels(self.page)
        
        self.create_ui()
        self.load_thumbnails()

    def create_ui(self):
        self.canvas = Canvas(self.top, bg='white')
        self.canvas.pack(side='left', fill='both', expand=True)

        self.scrollbar = Scrollbar(self.top, orient='vertical', command=self.canvas.yview)
        self.scrollbar.pack(side='right', fill='y')

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        button_frame = tk.Frame(self.top)
        button_frame.pack(side='bottom', fill='x')

        self.move_up_button = Button(button_frame, text="Subir", command=self.move_up)
        self.move_up_button.pack(side='left')

        self.move_down_button = Button(button_frame, text="Bajar", command=self.move_down)
        self.move_down_button.pack(side='left')

        self.auto_order_button = Button(button_frame, text="Ordenar Automáticamente", command=self.auto_order)
        self.auto_order_button.pack(side='left')

        self.reorder_all_button = Button(button_frame, text="Reordenar y Guardar Todas las Tareas Restantes", command=self.reorder_and_save_all)
        self.reorder_all_button.pack(side='left')

        self.save_button = Button(button_frame, text="Guardar", command=self.save_and_close)
        self.save_button.pack(side='right')

    def calculate_angle_and_hypotenuse(self, x, y):
        hypotenuse = math.sqrt(x**2 + y**2)
        angle = math.degrees(math.atan2(y, x))
        return angle, hypotenuse

    def load_thumbnails(self):
        self.canvas.delete('all')
        self.thumbnails = []
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            image = Image.open(self.panel_manager.get_page_path(self.page)).crop((x1, y1, x2, y2))
            thumbnail = ImageTk.PhotoImage(image.resize((100, 100), Image.LANCZOS))
            self.thumbnails.append(thumbnail)
            self.canvas.create_image(10, i * 170 + 10, image=thumbnail, anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            
            angle, hypotenuse = self.calculate_angle_and_hypotenuse(x1, y1)
            
            self.canvas.create_text(120, i * 170 + 10, text=f"Panel {i + 1}", anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            self.canvas.create_text(120, i * 170 + 30, text=f"Coords: ({x1}, {y1})", anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            self.canvas.create_text(120, i * 170 + 50, text=f"Ángulo: {angle:.2f}°", anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            self.canvas.create_text(120, i * 170 + 70, text=f"Hipotenusa: {hypotenuse:.2f}", anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            
            self.canvas.tag_bind(f'thumbnail{i}', '<Button-1>', lambda event, index=i: self.on_thumbnail_click(index))
        
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    def on_thumbnail_click(self, index):
        self.selected_index = index
        self.update_selection()

    def update_selection(self):
        self.canvas.delete('selection')
        if self.selected_index is not None:
            x1, y1, x2, y2 = 5, self.selected_index * 170 + 5, 115, self.selected_index * 170 + 115
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue', width=2, tags='selection')

    def save_and_close(self):
        new_order = [self.panel_images[i] for i in range(len(self.panel_images))]
        self.save_callback(self.page, new_order)
        self.top.destroy()

    def reorder_and_save_all(self):
        self.reorder_all_callback()
        self.top.destroy()

    @log_function  
    def update_thumbnails_order(self):
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            self.canvas.moveto(f'thumbnail{i}', 10, i * 170 + 10)
            self.canvas.itemconfig(f'thumbnail{i}', text=f"Panel {i + 1}")
            angle, hypotenuse = self.calculate_angle_and_hypotenuse(x1, y1)
            self.canvas.itemconfig(f'thumbnail{i}', text=f"Panel {i + 1}\nCoords: ({x1}, {y1})\nÁngulo: {angle:.2f}°\nHipotenusa: {hypotenuse:.2f}")
        
        self.canvas.config(scrollregion=self.canvas.bbox('all'))

    @log_function  
    def auto_order(self):
        def group_into_rows(panels, y_tolerance=50):
            sorted_panels = sorted(panels, key=lambda p: (p[1], p[0]))
            rows = []
            current_row = [sorted_panels[0]]
            for panel in sorted_panels[1:]:
                if abs(panel[1] - current_row[0][1]) <= y_tolerance:
                    current_row.append(panel)
                else:
                    rows.append(sorted(current_row, key=lambda p: p[0]))
                    current_row = [panel]
            if current_row:
                rows.append(sorted(current_row, key=lambda p: p[0]))
            return rows
    
        ordered_rows = group_into_rows(self.panel_images)
        self.panel_images = [panel for row in ordered_rows for panel in row]
        
        self.load_thumbnails()
        self.selected_index = None
        self.update_thumbnails_order()
        messagebox.showinfo("Ordenamiento Automático", "Los paneles han sido reordenados automáticamente. Por favor, revise el orden y guarde si está de acuerdo.")

    @log_function  
    def move_up(self):
        if self.selected_index is not None and self.selected_index > 0:
            self.panel_images[self.selected_index], self.panel_images[self.selected_index - 1] = \
                self.panel_images[self.selected_index - 1], self.panel_images[self.selected_index]
            self.selected_index -= 1
            self.update_thumbnails_order()
            self.update_selection()

    @log_function  
    def move_down(self):
        if self.selected_index is not None and self.selected_index < len(self.panel_images) - 1:
            self.panel_images[self.selected_index], self.panel_images[self.selected_index + 1] = \
                self.panel_images[self.selected_index + 1], self.panel_images[self.selected_index]
            self.selected_index += 1
            self.update_thumbnails_order()
            self.update_selection()






















