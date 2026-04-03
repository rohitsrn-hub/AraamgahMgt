@echo off
REM E-ARMS Local Startup Script for Windows
REM This script starts all required services for E-ARMS

echo ================================================
echo       Starting E-ARMS Locally (Windows)
echo ================================================
echo.

REM Check if MongoDB is running
echo [1] Checking MongoDB...
sc query MongoDB | find "RUNNING" >nul
if %errorlevel% equ 0 (
    echo [OK] MongoDB is running
) else (
    echo Starting MongoDB...
    net start MongoDB
    if %errorlevel% neq 0 (
        echo [ERROR] Failed to start MongoDB
        echo Please start MongoDB manually or run as Administrator
        pause
        exit /b 1
    )
)

REM Get local IP address
echo.
echo [2] Detecting local IP address...
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /c:"IPv4 Address"') do (
    set LOCAL_IP=%%a
    goto :found_ip
)
:found_ip
REM Trim spaces
for /f "tokens=* delims= " %%a in ("%LOCAL_IP%") do set LOCAL_IP=%%a

echo [OK] Your local IP: %LOCAL_IP%
echo      Access from other devices: http://%LOCAL_IP%:3000
echo.

REM Configure firewall (optional - requires admin)
echo [3] Configuring Windows Firewall...
netsh advfirewall firewall show rule name="E-ARMS Frontend" >nul 2>&1
if %errorlevel% neq 0 (
    echo Adding firewall rules (requires admin)...
    netsh advfirewall firewall add rule name="E-ARMS Frontend" dir=in action=allow protocol=TCP localport=3000 >nul 2>&1
    netsh advfirewall firewall add rule name="E-ARMS Backend" dir=in action=allow protocol=TCP localport=8001 >nul 2>&1
    echo [OK] Firewall rules added
) else (
    echo [OK] Firewall rules already exist
)

REM Start Backend
echo.
echo [4] Starting Backend...
cd backend
start "E-ARMS Backend" cmd /k python server.py
echo [OK] Backend started in new window

REM Wait for backend
timeout /t 3 /nobreak >nul

REM Create frontend .env.local if not exists
cd ..\frontend
if not exist .env.local (
    echo [INFO] Creating .env.local...
    echo REACT_APP_BACKEND_URL=http://%LOCAL_IP%:8001 > .env.local
)

REM Start Frontend
echo.
echo [5] Starting Frontend...
start "E-ARMS Frontend" cmd /k yarn start
echo [OK] Frontend started in new window

echo.
echo ================================================
echo      E-ARMS is starting successfully!
echo ================================================
echo.
echo Access URLs:
echo   - Local:    http://localhost:3000
echo   - Network:  http://%LOCAL_IP%:3000
echo.
echo Backend API: http://%LOCAL_IP%:8001
echo.
echo Two new windows opened for Backend and Frontend
echo Close those windows to stop the services
echo.
pause
