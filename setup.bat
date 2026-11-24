@echo off
setlocal
cd /d "%~dp0"

py -m venv .venv
if errorlevel 1 (
    echo Failed to create virtual environment. Check that Python is installed and available with the py launcher.
    pause
    exit /b 1
)

call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
if errorlevel 1 (
    echo Dependency installation failed. Check the error above.
    pause
    exit /b 1
)

echo.
echo AirScroll setup completed. Run run.bat to start it.
pause
