import os
import subprocess
import requests
import base64
import json
import time

# Configuración
GITHUB_REPO = "srexcel/ComicViewer"
GITHUB_TOKEN = "tu_token_de_github"  # Reemplaza con tu token de acceso personal de GitHub
API_URL = f"https://api.github.com/repos/{GITHUB_REPO}"

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode(), error.decode()

def get_file_sha(path):
    url = f"{API_URL}/contents/{path}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json()["sha"]
    return None

def create_or_update_file(path, content):
    url = f"{API_URL}/contents/{path}"
    sha = get_file_sha(path)
    data = {
        "message": f"Update {path}",
        "content": base64.b64encode(content.encode()).decode()
    }
    if sha:
        data["sha"] = sha
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.put(url, headers=headers, data=json.dumps(data))
    if response.status_code not in [200, 201]:
        print(f"Error creating/updating file {path}: {response.json()}")
    else:
        print(f"Successfully created/updated {path}")

def create_workflow_file():
    workflow_content = """
name: Build ComicViewer Executable

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  build:
    runs-on: windows-latest
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.10'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: |
        pyinstaller --onefile --windowed --add-data "*.json;." --add-data "*.txt;." --add-data "ComicViewer.py;." --name ComicViewer main.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: ComicViewer
        path: dist/ComicViewer.exe
    """
    create_or_update_file(".github/workflows/build.yml", workflow_content)

def create_requirements_file():
    output, _ = run_command("pip freeze")
    create_or_update_file("requirements.txt", output)

def trigger_workflow():
    url = f"{API_URL}/dispatches"
    data = {
        "event_type": "build_executable"
    }
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    response = requests.post(url, headers=headers, data=json.dumps(data))
    if response.status_code == 204:
        print("Workflow triggered successfully")
    else:
        print(f"Error triggering workflow: {response.json()}")

def check_workflow_status():
    url = f"{API_URL}/actions/runs"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    for _ in range(10):  # Check status for up to 5 minutes
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            runs = response.json()["workflow_runs"]
            if runs:
                latest_run = runs[0]
                if latest_run["status"] == "completed":
                    if latest_run["conclusion"] == "success":
                        print("Executable created successfully")
                        return True
                    else:
                        print("Workflow failed")
                        return False
        time.sleep(30)  # Wait 30 seconds before checking again
    print("Timed out waiting for workflow to complete")
    return False

def main():
    create_workflow_file()
    create_requirements_file()
    trigger_workflow()
    if check_workflow_status():
        print("You can now download the executable from the GitHub Actions page")

if __name__ == "__main__":
    main()