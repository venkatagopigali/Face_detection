@echo off
title Face Recognition Attendance System
color 0A
echo.
echo  =====================================================
echo   Face Recognition Attendance Management System
echo  =====================================================
echo.
echo  Starting server... Please wait.
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py

echo.
echo  Server stopped. Press any key to exit.
pause >nul
