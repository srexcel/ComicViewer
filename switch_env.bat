
@echo off
REM Activar el entorno comicviewer
call conda activate comicviewer

REM Ejecutar el script create_exe.py
python D:/Compartida/Python/ComicViewer_Repo/create_exe.py

REM Verificar si el script create_exe.py se ejecutó correctamente
IF %ERRORLEVEL% NEQ 0 (
    echo Error al ejecutar create_exe.py. No se cambiará al entorno original.
    pause
    exit /b %ERRORLEVEL%
)

REM Regresar al entorno base
call conda deactivate

echo Script completado.
pause
