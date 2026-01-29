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
echo IOC Scanner - Fix Firewall Rules
echo ========================================
echo.
echo Adding Windows Firewall rules...
echo.

:: Add firewall rules for ports 3000 and 8000
powershell -Command "New-NetFirewallRule -DisplayName 'WSL Dashboard Port 3000' -Direction Inbound -LocalPort 3000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Firewall rule added for port 3000
) else (
    echo [INFO] Firewall rule for port 3000 already exists or created
)

powershell -Command "New-NetFirewallRule -DisplayName 'WSL API Port 8000' -Direction Inbound -LocalPort 8000 -Protocol TCP -Action Allow -ErrorAction SilentlyContinue" >nul 2>&1
if %errorLevel% equ 0 (
    echo [OK] Firewall rule added for port 8000
) else (
    echo [INFO] Firewall rule for port 8000 already exists or created
)

echo.
echo ========================================
echo Firewall rules configured!
echo ========================================
echo.
echo You can now access:
echo   Dashboard: http://localhost:3000
echo   API:       http://localhost:8000
echo.
echo If you still get ERR_CONNECTION_RESET:
echo   1. Make sure port forwarding is set up (run FIX_NOW.bat)
echo   2. Check that services are running in WSL
echo   3. Try accessing via WSL IP: http://172.17.32.19:3000
echo.
pause
