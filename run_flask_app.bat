@echo off
setlocal

echo ========================================
echo   FLASK APP LAUNCHER - ONE CLICK START
echo ========================================

:: Step 1: First-time setup if needed
if not exist "venv" (
    echo [*] First-time setup detected...
    echo [*] Creating virtual environment...
    python -m venv venv

    echo [*] Activating environment...
    call venv\Scripts\activate.bat

    if exist requirements.txt (
        echo [*] Installing required packages...
        pip install -r requirements.txt
    ) else (
        echo [!] No requirements.txt found. Skipping package installation.
    )
) else (
    echo [*] Environment found. Activating...
    call venv\Scripts\activate.bat
)

:: Step 2: Run Flask app using Python in background (delayed start)
echo [*] Starting Flask app...
start "FlaskApp" cmd /k "python main.py"

:: Step 3: Wait for server to start (you can adjust timeout)
timeout /t 3 > nul

:: Step 4: Open browser to the Flask app
start "" http://127.0.0.1:5000

echo [*] Browser opened. Flask app is running.
echo --------------------------------------------
echo   View logs in the Flask window (above)
echo   Close it or press Ctrl+C to stop the app
echo --------------------------------------------

endlocal
