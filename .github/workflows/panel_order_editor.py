from tkinter import Toplevel, BOTH, Canvas, Button, Listbox, LEFT, SINGLE

class PanelOrderEditor:
    def __init__(self, master, panel_manager, current_page, save_callback):
        self.top = Toplevel(master)
        self.top.title("Reordenar Paneles")
        self.panel_manager = panel_manager
        self.current_page = current_page
        self.save_callback = save_callback

        self.canvas = Canvas(self.top, bg='white')
        self.canvas.pack(fill=BOTH, expand=1)

        self.listbox = Listbox(self.canvas, selectmode=SINGLE)
        self.listbox.pack(fill=BOTH, expand=1)

        self.load_current_order()

        self.move_up_button = Button(self.top, text="Subir", command=self.move_up)
        self.move_up_button.pack(side=LEFT)

        self.move_down_button = Button(self.top, text="Bajar", command=self.move_down)
        self.move_down_button.pack(side=LEFT)

        self.save_button = Button(self.top, text="Guardar", command=self.save_and_close)
        self.save_button.pack(side=LEFT)

    def load_current_order(self):
        self.listbox.delete(0, 'end')
        for i, _ in enumerate(self.panel_manager.get_panels(self.current_page)):
            self.listbox.insert('end', f"Panel {i + 1}")

    def move_up(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            if index > 0:
                self.swap_items(index, index - 1)

    def move_down(self):
        selected = self.listbox.curselection()
        if selected:
            index = selected[0]
            if index < self.listbox.size() - 1:
                self.swap_items(index, index + 1)

    def swap_items(self, index1, index2):
        items = self.listbox.get(0, 'end')
        items = list(items)
        items[index1], items[index2] = items[index2], items[index1]
        self.listbox.delete(0, 'end')
        for item in items:
            self.listbox.insert('end', item)
        self.listbox.selection_set(index2)

    def save_and_close(self):
        new_order = self.listbox.curselection()
        self.save_callback(new_order)
        self.top.destroy()
