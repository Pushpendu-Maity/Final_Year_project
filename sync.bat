@echo off
setlocal
echo ======================================================================
echo           ONE-CLICK AUTO-SYNC TO GITHUB (Final_Year_project)
echo ======================================================================
echo.

cd /d "%~dp0"

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git is not installed or not detected in Windows PATH.
    echo Please install Git for Windows: https://git-scm.com/download/win
    echo (Make sure to check "Add Git to PATH" during installation)
    echo Then run this file again.
    echo.
    pause
    exit /b 1
)

echo [1/3] Staging all modified project files...
git add .

echo [2/3] Creating auto-commit...
for /f "tokens=2 delims==" %%I in ('wmic os get localdatetime /value') do set datetime=%%I
set timestamp=%datetime:~0,4%-%datetime:~4,2%-%datetime:~6,2% %datetime:~8,2%:%datetime:~10,2%
git commit -m "Auto-update: %timestamp%"

echo [3/3] Pushing to GitHub (Pushpendu-Maity/Final_Year_project)...
git push origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ======================================================================
    echo  [SUCCESS] All project updates successfully synced to GitHub!
    echo  View online: https://github.com/Pushpendu-Maity/Final_Year_project
    echo ======================================================================
) else (
    echo.
    echo [NOTICE] If prompted by Windows, sign in to your GitHub account once.
)

echo.
timeout /t 5
