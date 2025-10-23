@echo off
echo Building IsoQuant...
echo.

REM Check if Python 3.11 is available
py -3.11 --version >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python 3.11 not found! Using default Python...
    python --version
    python -m PyInstaller IsoQuant.spec
) else (
    echo Using Python 3.11...
    py -3.11 -m PyInstaller IsoQuant.spec
)

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ========================================
    echo SUCCESS! Executable created in dist\IsoQuant.exe
    echo ========================================
) else (
    echo.
    echo ========================================
    echo ERROR during compilation
    echo ========================================
)

pause
