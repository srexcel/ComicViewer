import os
import subprocess
import sys

def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    output, error = process.communicate()
    return output.decode('utf-8'), error.decode('utf-8'), process.returncode

def update_requirements():
    requirements = """annotated-types==0.7.0
anyio==3.7.1
certifi==2024.7.4
chardet==3.0.4
charset-normalizer==3.3.2
click==8.1.7
colorama==0.4.6
deepl==1.18.0
distro==1.9.0
exceptiongroup==1.2.2
googletrans==4.0.0rc1
h11==0.9.0
h2==3.2.0
hpack==3.0.0
hstspreload==2024.7.1
httpcore==0.9.1
httpx==0.13.3
hyperframe==5.2.0
idna==2.10
libretranslatepy==2.1.1
lxml==5.2.2
numpy==2.0.0
openai==0.7.0
opencv-python==4.10.0.84
packaging==24.1
pillow==10.4.0
pydantic==2.8.2
pydantic-core==2.20.1
pyperclip==1.9.0
pytesseract==0.3.10
rarfile==4.2
requests==2.32.3
rfc3986==1.5.0
sniffio==1.3.1
tqdm==4.66.4
translate==3.6.1
typing-extensions==4.12.2
urllib3==2.2.2
Flask==2.0.1"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("requirements.txt updated.")

def update_github_workflow():
    workflow = """name: Build ComicViewer Executable

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
        python-version: '3.10.14'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pyinstaller
    
    - name: Build executable
      run: |
        pyinstaller --onefile --windowed --add-data "*.json;." --add-data "*.txt;." --add-data "*.py;." --hidden-import rarfile --name ComicViewer main.py
    
    - name: Upload artifact
      uses: actions/upload-artifact@v2
      with:
        name: ComicViewer
        path: dist/ComicViewer.exe"""
    
    os.makedirs('.github/workflows', exist_ok=True)
    with open('.github/workflows/build.yml', 'w') as f:
        f.write(workflow)
    print("GitHub Actions workflow updated.")

def setup_git():
    if not os.path.exists('.git'):
        run_command('git init')
        print("Git repository initialized.")
    
    run_command('git add .')
    print("All files added to staging.")
    
    run_command('git commit -m "Initial commit with updated files for GitHub Actions"')
    print("Changes committed.")

def push_to_github(repo_url):
    output, _, _ = run_command('git remote -v')
    if 'origin' not in output:
        run_command(f'git remote add origin {repo_url}')
        print("GitHub remote added.")
    
    output, error, returncode = run_command('git push -u origin main')
    if returncode == 0:
        print("Successfully pushed to GitHub.")
    else:
        print(f"Error pushing to GitHub: {error}")

def main():
    repo_url = "https://github.com/srexcel/ComicViewer.git"
    
    update_requirements()
    update_github_workflow()
    setup_git()
    push_to_github(repo_url)

if __name__ == "__main__":
    main()