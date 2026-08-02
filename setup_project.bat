@echo off
setlocal

cd /d "%~dp0"

echo ============================================
echo  TongaLang Project Setup
echo ============================================
echo.

where py >nul 2>nul
if %errorlevel%==0 (
    set "PYTHON_CMD=py -3"
) else (
    where python >nul 2>nul
    if %errorlevel%==0 (
        set "PYTHON_CMD=python"
    ) else (
        echo Error: Python was not found.
        echo Please install Python 3.10 or newer from https://www.python.org/downloads/
        echo During installation, tick "Add python.exe to PATH".
        pause
        exit /b 1
    )
)

echo Checking Python...
%PYTHON_CMD% --version
if errorlevel 1 (
    echo Error: Python is installed but could not be started.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo.
    echo Creating virtual environment in .venv...
    %PYTHON_CMD% -m venv .venv
    if errorlevel 1 (
        echo Error: Failed to create the virtual environment.
        pause
        exit /b 1
    )
) else (
    echo.
    echo Existing virtual environment found: .venv
)

echo.
echo Upgrading pip...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 (
    echo Error: Failed to upgrade pip.
    pause
    exit /b 1
)

echo.
echo Installing project dependencies...
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 (
    echo Error: Failed to install dependencies from requirements.txt.
    pause
    exit /b 1
)

echo.
echo ============================================
echo  Setup complete.
echo ============================================
echo.
echo Run the TongaLang IDE:
echo   .venv\Scripts\python.exe -m gui.app
echo.
echo Run an example program:
echo   .venv\Scripts\python.exe main.py examples\01_mazyina.tg
echo.
echo Run tests:
echo   .venv\Scripts\python.exe -m pytest -q
echo.

pause
endlocal
