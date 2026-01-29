# IOC Scanner - Port Forwarding Setup Script
# Run this script as Administrator in PowerShell

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "IOC Scanner - Port Forwarding Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "ERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host ""
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host "Then run this script again." -ForegroundColor Yellow
    exit 1
}

# Get WSL IP address
Write-Host "Getting WSL IP address..." -ForegroundColor Yellow
$wslIp = (wsl hostname -I).Trim().Split(' ')[0]

if (-not $wslIp) {
    Write-Host "ERROR: Could not get WSL IP address!" -ForegroundColor Red
    Write-Host "Make sure WSL is running." -ForegroundColor Yellow
    exit 1
}

Write-Host "WSL IP Address: $wslIp" -ForegroundColor Green
Write-Host ""

# Remove existing port forwarding rules
Write-Host "Removing existing port forwarding rules..." -ForegroundColor Yellow
netsh interface portproxy delete v4tov4 listenport=3000 listenaddress=0.0.0.0 2>$null
netsh interface portproxy delete v4tov4 listenport=8000 listenaddress=0.0.0.0 2>$null

# Add new port forwarding rules
Write-Host "Setting up port forwarding..." -ForegroundColor Yellow
netsh interface portproxy add v4tov4 listenport=3000 listenaddress=0.0.0.0 connectport=3000 connectaddress=$wslIp
netsh interface portproxy add v4tov4 listenport=8000 listenaddress=0.0.0.0 connectport=8000 connectaddress=$wslIp

Write-Host ""
Write-Host "Port forwarding configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "You can now access:" -ForegroundColor Cyan
Write-Host "  Dashboard: http://localhost:3000" -ForegroundColor White
Write-Host "  API:       http://localhost:8000" -ForegroundColor White
Write-Host "  API Docs:  http://localhost:8000/docs" -ForegroundColor White
Write-Host ""
Write-Host "If your WSL IP changes, run this script again." -ForegroundColor Yellow
Write-Host ""

# Show current port forwarding rules
Write-Host "Current port forwarding rules:" -ForegroundColor Cyan
netsh interface portproxy show all
