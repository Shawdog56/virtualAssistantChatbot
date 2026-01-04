@echo off
echo ===========================================
echo   LIXIL Assistant - Sistema de Soporte
echo ===========================================
echo.
echo [1] Iniciar Asistente (Chatbot)
echo [2] Subir codigo a ESP32
echo [3] Subir codigo a Raspberry Pico W
echo [4] Salir
echo.
set /p opt="Selecciona una opcion: "

if %opt%==1 docker-compose up --build
if %opt%==2 docker-compose run chatbot python flash_device.py esp32
if %opt%==3 docker-compose run chatbot python flash_device.py pico
if %opt%==4 exit

pause