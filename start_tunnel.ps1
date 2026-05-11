# ============================================================
# GeoFense — Smart Tunnel Starter
# Starts Docker + Tunnel, then AUTO-UPDATES GitHub config
# with the new URL. Teachers get the new URL automatically.
# ============================================================

Write-Host ""
Write-Host "================================================" -ForegroundColor Cyan
Write-Host "   GeoFense Smart Tunnel" -ForegroundColor Cyan
Write-Host "================================================" -ForegroundColor Cyan
Write-Host ""

# ── Step 1: Start Docker stack ─────────────────────────────
Write-Host "[1/3] Starting Docker stack..." -ForegroundColor Yellow
docker-compose up -d
Write-Host "Docker stack is running." -ForegroundColor Green
Write-Host ""

# ── Step 2: Start tunnel and capture the URL ───────────────
Write-Host "[2/3] Starting Cloudflare Tunnel..." -ForegroundColor Yellow
Write-Host "      Waiting for URL (this takes ~10 seconds)..." -ForegroundColor Gray
Write-Host ""

$cloudflaredPath = "C:\Program Files (x86)\cloudflared\cloudflared.exe"
$logFile = "$env:TEMP\cloudflared_output.txt"

# Remove old log file
if (Test-Path $logFile) { Remove-Item $logFile -Force }

# Start cloudflared in background, redirect output to log file
$process = Start-Process -FilePath $cloudflaredPath `
    -ArgumentList "tunnel --url http://localhost:80" `
    -RedirectStandardError $logFile `
    -PassThru `
    -WindowStyle Hidden

# Poll the log file for the tunnel URL (up to 30 seconds)
$tunnelUrl = $null
$attempts = 0
while ($null -eq $tunnelUrl -and $attempts -lt 60) {
    Start-Sleep -Milliseconds 500
    $attempts++
    if (Test-Path $logFile) {
        $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        if ($content -match '\|\s+(https://[a-z0-9\-]+\.trycloudflare\.com)') {
            $tunnelUrl = $Matches[1]
        }
    }
}

if ($null -eq $tunnelUrl) {
    Write-Host "[ERROR] Could not get tunnel URL. Check cloudflared is installed." -ForegroundColor Red
    Write-Host "        Keeping existing URL in GitHub config unchanged." -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "*** YOUR LIVE URL ***" -ForegroundColor Green
    Write-Host "  $tunnelUrl" -ForegroundColor White
    Write-Host "  Admin Panel: $tunnelUrl/admin/" -ForegroundColor White
    Write-Host ""

    # ── Step 3: Auto-update GitHub config ──────────────────
    Write-Host "[3/3] Auto-updating GitHub config with new URL..." -ForegroundColor Yellow

    $configPath = "$PSScriptRoot\config\app_config.json"
    $configContent = @{
        base_url = "$tunnelUrl/api"
        version  = 1
    } | ConvertTo-Json -Compress

    Set-Content -Path $configPath -Value $configContent -Encoding UTF8

    # Git commit and push
    Push-Location $PSScriptRoot
    git add config/app_config.json | Out-Null
    git commit -m "Auto-update tunnel URL: $tunnelUrl" | Out-Null
    git push origin main | Out-Null
    Pop-Location

    Write-Host "GitHub config updated! Teachers will get the new URL automatically." -ForegroundColor Green
    Write-Host ""
    Write-Host "================================================" -ForegroundColor Cyan
    Write-Host "  Everything is LIVE. Keep this window open." -ForegroundColor Cyan
    Write-Host "  Closing this window = tunnel stops." -ForegroundColor Cyan
    Write-Host "================================================" -ForegroundColor Cyan
}

Write-Host ""
Write-Host "Press Ctrl+C to stop the tunnel." -ForegroundColor Gray

# Keep the process alive
$process.WaitForExit()
