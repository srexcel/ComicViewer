from tkinter import Toplevel, Canvas, Button, Scrollbar, VERTICAL, BOTH, Y
from PIL import Image, ImageTk

class PanelOrderEditor:
    def __init__(self, master, panel_manager, current_page, save_callback):
        self.top = Toplevel(master)
        self.top.title("Reordenar Paneles")
        self.panel_manager = panel_manager
        self.current_page = current_page
        self.save_callback = save_callback
        self.selected_index = None

        self.canvas = Canvas(self.top, bg='white')
        self.canvas.pack(side='left', fill=BOTH, expand=1)

        self.scrollbar = Scrollbar(self.top, orient=VERTICAL, command=self.canvas.yview)
        self.scrollbar.pack(side='left', fill=Y)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.load_thumbnails()

        self.move_up_button = Button(self.top, text="Subir", command=self.move_up)
        self.move_up_button.pack(side='left')

        self.move_down_button = Button(self.top, text="Bajar", command=self.move_down)
        self.move_down_button.pack(side='left')

        self.save_button = Button(self.top, text="Guardar", command=self.save_and_close)
        self.save_button.pack(side='left')

    def load_thumbnails(self):
        self.panel_images = self.panel_manager.get_panels(self.current_page)
        self.thumbnails = []
        self.canvas.delete('thumbnail')
        for i, (x1, y1, x2, y2) in enumerate(self.panel_images):
            image = Image.open(self.panel_manager.get_page_path(self.current_page)).crop((x1, y1, x2, y2))
            thumbnail = ImageTk.PhotoImage(image.resize((100, 100), Image.LANCZOS))
            self.thumbnails.append(thumbnail)
            self.canvas.create_image(10, i * 110 + 10, image=thumbnail, anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            self.canvas.create_text(10, i * 110 + 110, text=f"Panel {i + 1}", anchor='nw', tags=(f'thumbnail{i}', 'thumbnail'))
            self.canvas.tag_bind(f'thumbnail{i}', '<Button-1>', lambda event, index=i: self.on_thumbnail_click(index))

    def on_thumbnail_click(self, index):
        self.selected_index = index
        self.update_selection()

    def update_selection(self):
        self.canvas.delete('selection')
        if self.selected_index is not None:
            x1, y1, x2, y2 = 10, self.selected_index * 110 + 10, 110, self.selected_index * 110 + 110
            self.canvas.create_rectangle(x1, y1, x2, y2, outline='blue', width=2, tags='selection')

    def move_up(self):
        if self.selected_index is not None and self.selected_index > 0:
            index = self.selected_index
            self.panel_images[index], self.panel_images[index - 1] = self.panel_images[index - 1], self.panel_images[index]
            self.selected_index -= 1
            self.load_thumbnails()
            self.update_selection()

    def move_down(self):
        if self.selected_index is not None and self.selected_index < len(self.panel_images) - 1:
            index = self.selected_index
            self.panel_images[index], self.panel_images[index + 1] = self.panel_images[index + 1], self.panel_images[index]
            self.selected_index += 1
            self.load_thumbnails()
            self.update_selection()

    def save_and_close(self):
        self.save_callback([self.panel_images.index(panel) for panel in self.panel_images])
        self.top.destroy()
