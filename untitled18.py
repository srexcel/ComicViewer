# -*- coding: utf-8 -*-
"""
Created on Fri Jul 19 23:17:00 2024

@author: Usuario
"""

import subprocess
import sys

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

def check_installed_packages():
    """Obtiene la lista de paquetes instalados en el entorno actual."""
    installed_packages = {}
    result = subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=True, text=True)
    for line in result.stdout.splitlines()[2:]:
        package, version = line.split()[:2]
        installed_packages[package.lower()] = version
    return installed_packages

def check_and_install_dependencies(required_dependencies):
    """Verifica las dependencias requeridas y las instala si faltan."""
    installed_packages = check_installed_packages()
    
    for dependency in required_dependencies:
        package_name = dependency.split('==')[0].lower()
        if package_name in installed_packages:
            print(f"{dependency} ya está instalado.")
        else:
            print(f"{dependency} no está instalado. Instalando...")
            run_command([sys.executable, '-m', 'pip', 'install', dependency])

def main():
    required_dependencies = [
        "Pillow",
        "pyperclip",
        "rarfile",
        "pytesseract",
        "googletrans==3.0.0",
        "requests",
        "deepl",
        "opencv-python",
        "openai"
    ]
    
    check_and_install_dependencies(required_dependencies)

if __name__ == "__main__":
    main()
