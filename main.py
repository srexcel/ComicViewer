from tkinter import Tk
from comic_viewer import ComicViewer
import constants
import rarfile  # Asegúrate de que rarfile está importado explícitamente

if __name__ == "__main__":
    root = Tk()
    root.geometry(constants.WINDOW_GEOMETRY)  # Ajustar la altura de la ventana inicial a 3.5 veces
    viewer = ComicViewer(root)
    root.mainloop()
