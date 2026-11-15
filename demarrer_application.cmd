@echo off
setlocal
cd /d "%~dp0webapp"
where node >nul 2>nul
if errorlevel 1 (
  echo Installer Node.js 22.13 ou superieur puis relancer ce fichier.
  pause
  exit /b 1
)
if not exist node_modules (
  call npm ci
  if errorlevel 1 exit /b 1
)
call npm run prepare-assets
if errorlevel 1 exit /b 1
echo Ouvrir http://127.0.0.1:5173 dans votre navigateur.
call npm run dev
