import tkinter as tk
from tkinter import messagebox  # Asegúrate de importar messagebox
from comic_viewer import ComicViewer
import logging
import platform
import sys
import os
import zipfile
from datetime import datetime

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

def save_scripts_to_zip():
    files_to_zip = [
        'main.py',
        'comic_viewer.py',
        'panel_manager.py',
        'panel_order_editor.py',
        'panel_recalculation.py',
        'state_manager.py',
        'translation_manager.py',
        'translation_configurator.py',
        'translation_editor.py',
        'utils.py',
        'logger.py'
    ]

    current_time = datetime.now()
    zip_filename = f"V_{current_time.year}_{current_time.month:02d}_{current_time.day:02d}_{current_time.hour:02d}{current_time.minute:02d}.zip"

    with zipfile.ZipFile(zip_filename, 'w') as zipf:
        for file in files_to_zip:
            if os.path.exists(file):
                zipf.write(file)
            else:
                logger.warning(f"File not found: {file}")

    logger.info(f"Scripts saved to {zip_filename}")
    return zip_filename

def on_closing(root, zip_filename):
    if messagebox.askyesno("Salir", "¿Deseas conservar el respaldo?"):
        root.destroy()
    else:
        os.remove(zip_filename)
        root.destroy()

if __name__ == "__main__":
    zip_filename = save_scripts_to_zip()

    root = tk.Tk()
    viewer = ComicViewer(root)
    root.geometry("1400x1000")
    logger.info("ComicViewer application started")
    root.protocol("WM_DELETE_WINDOW", lambda: on_closing(root, zip_filename))
    root.mainloop()
