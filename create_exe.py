import os
import subprocess
import sys
import shutil
import argparse
from pathlib import Path

def run_command(command):
    """Ejecuta un comando y retorna el resultado."""
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando el comando: {e}")
        print("Salida estándar:", e.stdout)
        print("Salida de error:", e.stderr)
        return False

def check_dependencies():
    """Verifica que todas las dependencias estén instaladas y reporta el resultado."""
    print("Verificando dependencias...")
    dependencies_status = {}
    with open('requirements.txt', 'r') as f:
        dependencies = f.read().splitlines()
    
    for dep in dependencies:
        package_name = dep.split('==')[0]
        try:
            __import__(package_name)
            dependencies_status[dep] = "OK"
        except ImportError:
            dependencies_status[dep] = "FALTA"
            print(f"  {dep} - FALTA. Instalando...")
            run_command([sys.executable, "-m", "pip", "install", dep])
    
    print("Resultado de la verificación de dependencias:")
    for dep, status in dependencies_status.items():
        print(f"  {dep} - {status}")

def clean_build_files():
    """Limpia los archivos generados durante la construcción."""
    dirs_to_remove = ['build', 'dist']
    files_to_remove = ['ComicViewer.spec', 'ComicViewer.exe']
    
    for dir_name in dirs_to_remove:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"Directorio {dir_name} eliminado.")
    
    for file_name in files_to_remove:
        if os.path.exists(file_name):
            os.remove(file_name)
            print(f"Archivo {file_name} eliminado.")

def create_spec_file():
    """Crea el archivo .spec inicial usando PyInstaller."""
    command = [
        "pyinstaller",
        "--name", "ComicViewer",
        "--onefile",
        "--add-data", "*.json;.",
        "--add-data", "*.txt;.",
        "--windowed",
        "--debug", "all",
        "main.py"
    ]
    print("Ejecutando PyInstaller para crear el archivo .spec:")
    print(" ".join(command))
    result = run_command(command)
    if result:
        print("Archivo .spec creado con éxito.")
    else:
        print("Hubo un error al crear el archivo .spec.")
    return result

def modify_spec_file():
    """Modifica el archivo .spec para incluir pyperclip."""
    spec_file = Path("ComicViewer.spec")
    if not spec_file.exists():
        print("Error: El archivo .spec no fue encontrado.")
        return False
    
    with open(spec_file, "r") as file:
        spec_content = file.read()
    
    hidden_imports_section = "hiddenimports=[]"
    hidden_imports_replacement = "hiddenimports=['pyperclip']"

    if hidden_imports_section in spec_content:
        spec_content = spec_content.replace(hidden_imports_section, hidden_imports_replacement)
    else:
        print("Advertencia: No se encontró la sección hiddenimports en el archivo .spec.")
    
    with open(spec_file, "w") as file:
        file.write(spec_content)
    
    print("Archivo .spec modificado para incluir pyperclip.")
    return True

def build_executable():
    """Crea el ejecutable usando el archivo .spec modificado."""
    command = ["pyinstaller", "ComicViewer.spec"]
    print("Ejecutando PyInstaller con el archivo .spec modificado:")
    result = run_command(command)
    return result

def main():
    parser = argparse.ArgumentParser(description="Crea un ejecutable para ComicViewer.")
    parser.add_argument("--debug", action="store_true", help="Crea una versión de depuración (sin --windowed)")
    parser.add_argument("--clean", action="store_true", help="Limpia los archivos de construcción anteriores")
    args = parser.parse_args()
    
    if args.clean:
        clean_build_files()
    
    check_dependencies()
    
    if create_spec_file() and modify_spec_file():
        if build_executable():
            print("Ejecutable creado con éxito.")
            dist_exe_path = Path.cwd() / "dist" / "ComicViewer.exe"
            if dist_exe_path.exists():
                try:
                    shutil.move(dist_exe_path, Path.cwd() / "ComicViewer.exe")
                    print(f"Ejecutable movido a: {Path.cwd() / 'ComicViewer.exe'}")
                except Exception as e:
                    print(f"Error moviendo el ejecutable: {e}")
            else:
                print(f"El ejecutable no se encontró en {dist_exe_path}")
        else:
            print("Hubo un error al crear el ejecutable.")
            print("Por favor, revise los mensajes de error anteriores para más detalles.")
    else:
        print("Hubo un error en el proceso de creación o modificación del archivo .spec.")
        return

    # Ejecutar el ejecutable creado y capturar cualquier error
    print("Ejecutando el ejecutable creado...")
    exe_path = Path.cwd() / "ComicViewer.exe"
    try:
        result = subprocess.run([exe_path], check=True, capture_output=True, text=True)
        print("Ejecutable ejecutado exitosamente.")
        print("Salida estándar:", result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando el ejecutable: {e}")
        print("Salida estándar:", e.stdout)
        print("Salida de error:", e.stderr)

if __name__ == "__main__":
    main()
