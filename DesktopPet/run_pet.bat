@echo off
setlocal enabledelayedexpansion
title run_pet

cd /d "%~dp0"

:: 1. Detect Python
set "PYTHON_EXE="
if exist "%USERPROFILE%\miniconda3\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\miniconda3\python.exe"
) else if exist "%USERPROFILE%\anaconda3\python.exe" (
    set "PYTHON_EXE=%USERPROFILE%\anaconda3\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python312\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
) else if exist "%LOCALAPPDATA%\Programs\Python\Python310\python.exe" (
    set "PYTHON_EXE=%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
) else if exist "C:\Program Files\Python312\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Python312\python.exe"
) else if exist "C:\Program Files\Python311\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Python311\python.exe"
) else if exist "C:\Program Files\Python310\python.exe" (
    set "PYTHON_EXE=C:\Program Files\Python310\python.exe"
)

if "!PYTHON_EXE!"=="" (
    py -3 --version >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_EXE=py -3"
    )
)

if "!PYTHON_EXE!"=="" (
    python -c "import sys; print(sys.executable)" >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        for /f "tokens=*" %%i in ('python -c "import sys; print(sys.executable)" 2^>nul') do (
            set "PYTHON_EXE=%%i"
        )
    )
)

if "!PYTHON_EXE!"=="" (
    echo [ERROR] Python was not found. Please install Python 3.10+
    pause
    exit /b 1
)

:: 2. Auto-verify dependencies in background
if exist "tools\setup_and_run.py" (
    "!PYTHON_EXE!" tools\setup_and_run.py --no-launch >nul 2>&1
) else if exist "setup_and_run.py" (
    "!PYTHON_EXE!" setup_and_run.py --no-launch >nul 2>&1
)

:: 3. Launch main.py completely detached from console/terminal with job breakaway
set "PYTHONW_EXE=!PYTHON_EXE:python.exe=pythonw.exe!"
if not exist "!PYTHONW_EXE!" set "PYTHONW_EXE=!PYTHON_EXE!"

"!PYTHON_EXE!" -c "import subprocess; flags = 0x08 | 0x0200 | 0x01000000; subprocess.Popen([r'!PYTHONW_EXE!', 'main.py'], creationflags=flags)" >nul 2>&1

exit 0

