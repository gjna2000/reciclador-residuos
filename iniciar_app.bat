@echo off
setlocal
title EcoClasifica - Streamlit

rem Convierte la carpeta de este archivo a una ruta que WSL pueda usar.
for /f "delims=" %%I in ('wsl.exe wslpath -u "%~dp0."') do set "WSL_PROJECT_DIR=%%I"

if not defined WSL_PROJECT_DIR (
    echo No se pudo encontrar WSL. Verifica que WSL este instalado y configurado.
    pause
    exit /b 1
)

rem El trabajo de entorno e inicio vive en el script portable de Linux/WSL.
wsl.exe bash -lc "cd '%WSL_PROJECT_DIR%' && bash ./start_app.sh"

if errorlevel 1 (
    echo.
    echo EcoClasifica termino con un error. Revisa el mensaje anterior.
    pause
)

endlocal
