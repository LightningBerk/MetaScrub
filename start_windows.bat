@echo off
SETLOCAL EnableExtensions EnableDelayedExpansion

REM MetaScrub One-Click Launcher for Windows

cd /d "%~dp0"

REM Check if Python is installed
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

REM Check Python version (simple check, relies on python being available)
REM For a robust check we run a snippet
python -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python 3.8+ is required.
    python --version
    pause
    exit /b 1
)

SET "VENV_DIR=.venv"

REM Create virtual environment if it doesn't exist
IF NOT EXIST "%VENV_DIR%" (
    echo [INFO] Creating virtual environment...
    python -m venv "%VENV_DIR%"
)

REM Activate virtual environment
CALL "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip and install dependencies
echo [INFO] Checking dependencies...
python -m pip install --upgrade pip >nul
python -m pip install -e . >nul

REM Check for ffmpeg
where ffmpeg >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [INFO] ffmpeg not found. Attempting to install via winget...
    
    where winget >nul 2>&1
    IF !ERRORLEVEL! NEQ 0 (
        echo [WARNING] winget not found.
        GOTO :INSTALL_FFMPEG_DIRECT
    ) ELSE (
        winget install -e --id Gyan.FFmpeg --accept-package-agreements --accept-source-agreements
        IF !ERRORLEVEL! NEQ 0 (
            echo [WARNING] Failed to install ffmpeg via winget.
            GOTO :INSTALL_FFMPEG_DIRECT
        ) ELSE (
            echo [INFO] ffmpeg installed successfully.
            echo [INFO] Please restart this script to ensure ffmpeg is available in your PATH.
            pause
            exit /b 0
        )
    )
)

GOTO :LAUNCH_APP

:INSTALL_FFMPEG_DIRECT
echo [INFO] Attempting direct download of ffmpeg...
echo [INFO] Downloading https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip...
powershell -Command "$progressPreference = 'SilentlyContinue'; Invoke-WebRequest -Uri 'https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip' -OutFile 'ffmpeg.zip'"

IF NOT EXIST "ffmpeg.zip" (
    echo [ERROR] Download failed.
    ping -n 6 127.0.0.1 >nul
    GOTO :LAUNCH_APP
)

echo [INFO] Extracting ffmpeg...
powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force"

echo [INFO] Configuring ffmpeg...
REM Wait a moment for file locks to release
ping -n 3 127.0.0.1 >nul

REM Move the inner bin folder directly to 'ffmpeg'
powershell -Command "$sub = Get-ChildItem -Path 'ffmpeg_temp' -Directory | Select-Object -First 1; Move-Item -Path $sub.FullName -Destination 'ffmpeg' -Force"
rmdir /s /q "ffmpeg_temp"
del "ffmpeg.zip"

echo [INFO] Adding ffmpeg to PATH for this session...
SET "PATH=%~dp0ffmpeg\bin;%PATH%"

where ffmpeg >nul 2>&1
IF !ERRORLEVEL! EQU 0 (
    echo [INFO] ffmpeg installed and configured successfully!
) ELSE (
    echo [WARNING] Something went wrong configuring ffmpeg.
)

:LAUNCH_APP

REM Launch the application
echo [INFO] Starting MetaScrub...
python -m scrubmeta.gui

IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Application exited with error code %ERRORLEVEL%
    pause
)

ENDLOCAL
