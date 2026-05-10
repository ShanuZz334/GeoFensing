@echo off
echo ==========================================
echo   GeoFense - Starting Application Stack
echo ==========================================
echo.
docker-compose up -d
echo.
echo Application is starting...
echo Admin Panel: http://localhost/admin
echo Teacher Portal: http://localhost/teacher
echo API: http://localhost/health
echo.
echo To see logs, run: docker-compose logs -f
echo.
pause
