@echo off
:: Check for admin privileges
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ========================================
    echo ERROR: Administrator privileges required!
    echo ========================================
    echo.
    echo Please right-click this file and select
    echo "Run as Administrator"
    echo.
    pause
    exit /b 1
)

echo ========================================
echo IOC Scanner - Fix localhost Access
echo ========================================
echo.
echo Setting up port forwarding...
echo.

:: Get WSL IP address
echo Getting WSL IP address...
for /f "tokens=1" %%i in ('wsl hostname -I') do set WSL_IP=%%i
echo WSL IP: %WSL_IP%
echo.

:: Remove existing rules first
echo Removing existing port forwarding rules...
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 >nul 2>&1
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 >nul 2>&1

:: Add new port forwarding rules
echo Setting up port forwarding for Dashboard (port 3000)...
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=%WSL_IP%
if %errorLevel% equ 0 (
    echo [OK] Port 3000 forwarded
) else (
    echo [ERROR] Failed to forward port 3000
)

echo Setting up port forwarding for API (port 8000)...
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=%WSL_IP%
if %errorLevel% equ 0 (
    echo [OK] Port 8000 forwarded
) else (
    echo [ERROR] Failed to forward port 8000
)

echo.
echo ========================================
echo Port forwarding configured!
echo ========================================
echo.
echo You can now access:
echo   Dashboard: http://localhost:3000
echo   API:       http://localhost:8000
echo   API Docs:  http://localhost:8000/docs
echo.
echo Showing current port forwarding rules:
echo.
netsh interface portproxy show all
echo.
echo Press any key to open the dashboard in your browser...
pause >nul
start http://localhost:3000
