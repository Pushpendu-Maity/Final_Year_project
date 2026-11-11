@echo off
echo ======================================================================
echo        PUSH TO GITHUB REPOSITORY: Final_Year_project
echo ======================================================================
echo.

where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Git is not currently installed or not detected in Windows PATH.
    echo.
    echo Please download and install Git for Windows:
    echo https://git-scm.com/download/win
    echo.
    echo (Make sure to check "Add Git to PATH" during installation)
    echo Then run this script again!
    echo.
    pause
    exit /b 1
)

echo 1. Initializing Git repository...
if not exist .git (
    git init
    git branch -M main
    git remote add origin https://github.com/Pushpendu-Maity/Final_Year_project.git
) else (
    git remote set-url origin https://github.com/Pushpendu-Maity/Final_Year_project.git
)

echo 2. Staging all project files and modules...
git add .

echo 3. Creating commit...
git commit -m "Release: Intelligent Healthcare Recommendation System using Data Mining Techniques (7th Sem Major Project)"

echo 4. Pushing to GitHub (https://github.com/Pushpendu-Maity/Final_Year_project)...
echo Notice: If prompted, log in with your GitHub credentials or Personal Access Token.
git push -u origin main

echo.
echo ======================================================================
echo  Project successfully uploaded to:
echo  https://github.com/Pushpendu-Maity/Final_Year_project
echo ======================================================================
pause
