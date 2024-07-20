# -*- coding: utf-8 -*-
"""
Created on Tue Jul 16 23:06:21 2024

@author: Usuario
"""

import subprocess
import sys

def run_command(command):
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {' '.join(command)}")
        print(e.stderr)
        sys.exit(1)

def main():
    print("Desinstalando googletrans, httpcore, httpx y openai...")
    run_command([sys.executable, "-m", "pip", "uninstall", "-y", "googletrans", "httpcore", "httpx", "openai"])

    print("Instalando versiones específicas de httpcore y httpx...")
    run_command([sys.executable, "-m", "pip", "install", "httpcore==0.13.6"])
    run_command([sys.executable, "-m", "pip", "install", "httpx==0.18.2"])

    print("Instalando googletrans...")
    run_command([sys.executable, "-m", "pip", "install", "googletrans==4.0.0-rc1"])

    print("Instalando openai...")
    run_command([sys.executable, "-m", "pip", "install", "openai"])

    print("Verificando instalaciones...")
    run_command([sys.executable, "-m", "pip", "show", "googletrans"])
    run_command([sys.executable, "-m", "pip", "show", "httpcore"])
    run_command([sys.executable, "-m", "pip", "show", "httpx"])
    run_command([sys.executable, "-m", "pip", "show", "openai"])

if __name__ == "__main__":
    main()
