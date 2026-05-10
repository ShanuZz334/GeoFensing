@echo off
echo ================================================
echo   GeoFense - Starting Docker Stack + Tunnel
echo ================================================
echo.

echo [1/2] Starting Docker stack...
docker-compose up -d
echo.

echo [2/2] Starting Cloudflare Tunnel...
echo.
echo *** LOOK FOR YOUR URL IN THE OUTPUT BELOW ***
echo *** It will say: https://xxxx.trycloudflare.com ***
echo *** Copy that URL and update your Flutter app  ***
echo.
"C:\Program Files (x86)\cloudflared\cloudflared.exe" tunnel --url http://localhost:80

pause
