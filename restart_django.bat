@echo off
REM Script de redémarrage du serveur Django
echo.
echo ========================================
echo   Redemarrage du serveur Django
echo ========================================
echo.

REM Arrêter les processus Python sur le port 8000
echo Recherche des processus sur le port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do (
    echo Arret du processus PID %%a
    taskkill /F /PID %%a >nul 2>&1
)

timeout /t 2 /nobreak >nul

echo.
echo Demarrage du serveur Django...
echo.
echo La stacktrace complete s'affichera ci-dessous lors des erreurs
echo Appuyez sur Ctrl+C pour arreter le serveur
echo.
echo ========================================
echo.

python manage.py runserver 0.0.0.0:8000

pause

