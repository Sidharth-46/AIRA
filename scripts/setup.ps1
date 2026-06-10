<#
.SYNOPSIS
AIRA Setup Script for Windows (PowerShell)
#>

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "    AIRA - Think. Reason. Build." -ForegroundColor Cyan
Write-Host "    Initial Setup Script" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
Write-Host ""

# Check for Docker
if (!(Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "[!] Docker could not be found. Please install Docker Desktop first." -ForegroundColor Red
    exit 1
}

Write-Host "[*] Checking for .env file..." -ForegroundColor Yellow
if (!(Test-Path ".env")) {
    if (Test-Path ".env.example") {
        Write-Host "[*] Creating .env from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" -Destination ".env"
        Write-Host "[*] Please update .env with your specific configuration if necessary." -ForegroundColor Yellow
    } else {
        Write-Host "[!] .env.example not found. Please create a .env file." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[*] .env file already exists." -ForegroundColor Green
}

Write-Host "[*] Creating local data directories..." -ForegroundColor Yellow
$directories = @("data\uploads", "data\embeddings", "data\workspace", "logs")
foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Force -Path $dir | Out-Null
    }
}

Write-Host "[*] Setup complete." -ForegroundColor Green
Write-Host ""
Write-Host "To start AIRA, run:" -ForegroundColor Cyan
Write-Host "    docker-compose up -d --build" -ForegroundColor White
Write-Host ""
Write-Host "Once started, AIRA will be available at: http://localhost:3000" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan
