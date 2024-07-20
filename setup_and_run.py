import os
import sys
import subprocess
from github import Github

# Definir el nombre del repositorio y la ruta del archivo del token
GITHUB_REPO = "srexcel/ComicViewer"
TOKEN_FILE_PATH = r"D:\Compartida\Python\TOKEN_GIT.txt"

def run_command(command):
    try:
        output = subprocess.check_output(command, stderr=subprocess.STDOUT, universal_newlines=True)
        print(output)
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        print(f"Output: {e.output}")
        raise

def commit_and_push():
    # Añadir todos los archivos modificados
    run_command(["git", "add", "--all"])
    
    # Hacer commit y push
    run_command(["git", "commit", "-m", "Update files and GitHub Action workflow"])
    run_command(["git", "push"])

def create_github_action_workflow():
    workflow_dir = os.path.join(os.getcwd(), '.github', 'workflows')
    os.makedirs(workflow_dir, exist_ok=True)
    
    workflow_content = """
name: Build Executable

on:
  push:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.x'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable with PyInstaller
      run: pyinstaller --onefile --windowed --name=ComicViewer main.py
    
    - name: Create Release
      id: create_release
      uses: actions/create-release@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        tag_name: ${{ github.ref }}
        release_name: Release ${{ github.ref }}
        draft: false
        prerelease: false
    
    - name: Upload Release Asset
      uses: actions/upload-release-asset@v1
      env:
        GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
      with:
        upload_url: ${{ steps.create_release.outputs.upload_url }}
        asset_path: ./dist/ComicViewer.exe
        asset_name: ComicViewer.exe
        asset_content_type: application/vnd.microsoft.portable-executable
    """
    
    with open(os.path.join(workflow_dir, 'build.yml'), 'w') as f:
        f.write(workflow_content)

def get_github_token():
    try:
        with open(TOKEN_FILE_PATH, "r") as file:
            return file.read().strip()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo de token en {TOKEN_FILE_PATH}")
        sys.exit(1)

def main():
    github_token = get_github_token()
    
    try:
        print("Creando archivo de workflow para GitHub Actions...")
        create_github_action_workflow()
        
        print("Haciendo commit y push de los cambios...")
        commit_and_push()
        
        print("Proceso completado con éxito.")
        print("El ejecutable se creará automáticamente en GitHub cuando se haga push a la rama principal.")
    except Exception as e:
        print(f"Se produjo un error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
