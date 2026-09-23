@echo off
echo ===================================================
echo Starting Electronic Warfare Next.js Frontend...
echo ===================================================

cd /d "%~dp0\..\frontend"

if not exist "node_modules" (
    echo Installing frontend dependencies...
    call npm install
)

echo Starting Next.js development server on port 3000...
call npm run dev
