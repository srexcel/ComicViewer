import os
import subprocess
import logging

# Configurar logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configuración
project_dir = r"D:\Compartida\Python\ComicViewer_Git"
main_file = "comic_viewer.py"  # Asegúrate de que este sea el nombre correcto de tu archivo principal
output_dir = os.path.join(project_dir, "dist")

def create_exe():
    logger.info("Iniciando la creación del archivo .exe")
    
    # Cambia al directorio del proyecto
    os.chdir(project_dir)
    
    # Comando para crear el .exe
    cmd = [
        "pyinstaller",
        "--onefile",  # Crea un solo archivo ejecutable
        "--windowed",  # Para aplicaciones GUI (quita la consola)
        "--add-data", "*.json;.",  # Incluye archivos JSON si los hay
        "--add-data", "*.txt;.",   # Incluye archivos TXT si los hay
        "--name", "ComicViewer",   # Nombre del ejecutable
        main_file
    ]
    
    try:
        subprocess.run(cmd, check=True)
        logger.info(f"Archivo .exe creado exitosamente en {output_dir}")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error al crear el archivo .exe: {str(e)}")
    except Exception as e:
        logger.error(f"Error inesperado: {str(e)}")

if __name__ == "__main__":
    create_exe()