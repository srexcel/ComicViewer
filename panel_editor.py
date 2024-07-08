from tkinter import Toplevel, BOTH, Canvas, Button
from PIL import Image, ImageTk

class PanelEditor:
    def __init__(self, master, panel_manager, current_page):
        self.top = Toplevel(master)
        self.top.title("Corregir Paneles")
        self.top.geometry("1400x1050")
        self.panel_manager = panel_manager
        self.current_page = current_page
        self.current_rect = None
        self.rects = []
        self.canvas = Canvas(self.top, bg='white')
        self.canvas.pack(fill=BOTH, expand=1)
        self.canvas.bind("<Button-1>", self.start_draw)
        self.canvas.bind("<B1-Motion>", self.draw)
        self.canvas.bind("<ButtonRelease-1>", self.end_draw)

        self.load_page_image()
        self.draw_existing_panels()

        self.save_button = Button(self.top, text="Guardar", command=self.save_and_close)
        self.save_button.pack()

    def load_page_image(self):
        page_path = self.panel_manager.extract_page(self.current_page)
        self.image = Image.open(page_path)
        self.image_ratio = self.image.width / self.image.height
        self.tkimage = self.resize_image_to_canvas(self.image)
        self.canvas_image = self.canvas.create_image(0, 0, anchor='nw', image=self.tkimage)

    def resize_image_to_canvas(self, image):
        self.top.update()  # Asegúrate de que la ventana esté actualizada para obtener el tamaño correcto
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        canvas_ratio = canvas_width / canvas_height

        if self.image_ratio > canvas_ratio:
            new_width = canvas_width
            new_height = int(canvas_width / self.image_ratio)
        else:
            new_height = canvas_height
            new_width = int(canvas_height * self.image_ratio)

        self.scale_x = image.width / new_width
        self.scale_y = image.height / new_height

        return ImageTk.PhotoImage(image.resize((new_width, new_height), Image.Resampling.LANCZOS))

    def draw_existing_panels(self):
        self.rects = []
        for x1, y1, x2, y2 in self.panel_manager.get_panels(self.current_page):
            scaled_coords = self.scale_coords(x1, y1, x2, y2, invert=True)
            rect = self.canvas.create_rectangle(*scaled_coords, outline="red", width=5, tags="panel")
            self.rects.append(rect)

    def scale_coords(self, x1, y1, x2, y2, invert=False):
        if invert:
            return x1 / self.scale_x, y1 / self.scale_y, x2 / self.scale_x, y2 / self.scale_y
        else:
            return x1 * self.scale_x, y1 * self.scale_y, x2 * self.scale_x, y2 * self.scale_y

    def start_draw(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.current_rect = self.canvas.create_rectangle(self.start_x, self.start_y, self.start_x, self.start_y, outline="red", width=5)

    def draw(self, event):
        self.canvas.coords(self.current_rect, self.start_x, self.start_y, event.x, event.y)

    def end_draw(self, event):
        end_x, end_y = event.x, event.y
        new_panel = self.scale_coords(self.start_x, self.start_y, end_x, end_y)
        self.panel_manager.panel_corrections[self.current_page].append(new_panel)
        self.rects.append(self.canvas.create_rectangle(self.start_x, self.start_y, end_x, end_y, outline="red", width=5))
        print(f"Nuevo panel agregado: {new_panel}")

    def save_and_close(self):
        self.panel_manager.save_gui_file()
        self.top.destroy()
