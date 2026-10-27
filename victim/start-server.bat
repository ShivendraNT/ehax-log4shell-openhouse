@echo off
REM EHAX Open House - victim-side Minecraft 1.8.8 server launcher.
REM
REM Run this inside the isolated Windows victim VM from the logged-in user's
REM desktop. Minimise the console after startup; do not close it.
REM Put Java 8 on PATH, and put server.jar in this folder.

setlocal
set EHAX_LAB=1
set EHAX_PAYLOAD_DRY_RUN=0
set EHAX_PAYLOAD_SOUND=0

where java >nul 2>&1
if errorlevel 1 (
  echo [-] Java not found. Install Java 8 and add it to PATH.
  pause
  exit /b 1
)

if not exist server.jar (
  echo [-] server.jar is missing. Download Minecraft 1.8.8 server.jar here:
  echo     %CD%
  pause
  exit /b 1
)

if not exist server.properties (
  copy server.properties.template server.properties >nul
  echo [*] Created server.properties from the lab template.
)

if not exist eula.txt (
  echo # By setting eula=true you agree to the Minecraft EULA: https://aka.ms/MinecraftEULA> eula.txt
  echo eula=true>> eula.txt
  echo [*] Created eula.txt ^(eula=true^).
)

echo ============================================================
echo   EHAX // VICTIM MINECRAFT SERVER
echo ============================================================
echo   Lab guard  : EHAX_LAB=1
echo   JNDI trust : true ^(LAB ONLY^)
echo   Keep this console MINIMISED so the wallpaper is visible.
echo   Do not close it.
echo ============================================================
echo.

java -Dcom.sun.jndi.ldap.object.trustURLCodebase=true -Djava.net.preferIPv4Stack=true -Xms1024M -Xmx1024M -jar server.jar nogui
pause
