# ============================================================
# GeoFense — Permanent Institutional Tunnel
# Starts Docker + Permanent Cloudflare Tunnel
# ============================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   GeoFense Institutional Server" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Start Docker stack ─────────────────────────────
Write-Host "[1/2] Starting Docker stack..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "Docker stack is running." -ForegroundColor Green
Write-Host ""

# ── Step 2: Start Permanent Tunnel ─────────────────────────
Write-Host "[2/2] Starting Permanent Cloudflare Tunnel..." -ForegroundColor Yellow

$cloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$token = "eyJhIjoiMzIzZjA2NjQ1NWUyZDhmZWMyMmY3NDc5ZDE5MTJkMjkiLCJ0IjoiYTEzOWUwYTMtOTIwOC00MTEzLThkN2UtMzJkMTlhZDI2YWZiIiwicyI6Ik5qZ3laakE1Tm1ZdFlUVTFZaTAwTXpsaUxUazNabVV0TW1Oak1qTTBZemhoTlRVMiJ9"

# Kill any existing stale cloudflared processes to prevent file lock crashes
Get-Process -Name "cloudflared" -ErrorAction SilentlyContinue | Stop-Process -Force

# Start cloudflared in background
$process = Start-Process -FilePath $cloudflaredPath `
    -ArgumentList "tunnel run --token $token" `
    -PassThru `
    -WindowStyle Hidden

Write-Host ""
Write-Host "*** SERVER IS LIVE ***" -ForegroundColor Green
Write-Host "  API URL: https://api.praxistrade.website/api" -ForegroundColor White
Write-Host "  Admin Panel: https://api.praxistrade.website/admin/" -ForegroundColor White
Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "  Everything is LIVE. Keep this window open." -ForegroundColor Cyan
Write-Host "  Closing this window = tunnel stops." -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor Gray

# Keep the process alive
$process.WaitForExit()
