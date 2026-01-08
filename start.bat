@echo off
echo ========================================
echo   LogiTech Route Planning System
echo   Starting Application...
echo ========================================
echo.

REM Check if Docker is running
docker info >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [INFO] Docker is running...
echo.

REM Clean previous builds (optional - uncomment if needed)
REM echo [INFO] Cleaning previous containers...
REM docker-compose down -v

echo [INFO] Building and starting containers...
echo This may take 5-10 minutes on first run...
echo.

docker-compose up --build

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start services!
    echo Check the error messages above.
    pause
    exit /b 1
)

pause
