@echo off
setlocal
title Install Affinity Discord Rich Presence

echo.
echo Installing required Python packages...
py -3 -m pip install --user pypresence psutil
if errorlevel 1 (
    echo.
    echo Package installation failed. Make sure Python is installed and try again.
    pause
    exit /b 1
)

set "SCRIPT=%~dp0affinity_rpc.py"
if not exist "%SCRIPT%" (
    echo.
    echo Could not find affinity_rpc.py in this folder.
    pause
    exit /b 1
)

for /f "delims=" %%P in ('py -3 -c "import os,sys; print(os.path.join(os.path.dirname(sys.executable), 'pythonw.exe'))"') do set "PYTHONW=%%P"

if not exist "%PYTHONW%" (
    echo.
    echo Could not find pythonw.exe next to Python.
    echo Reinstall Python from https://www.python.org/downloads/ and enable the Python Launcher.
    pause
    exit /b 1
)

set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Affinity Discord RPC.lnk"

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
 "$ws = New-Object -ComObject WScript.Shell; $s = $ws.CreateShortcut($env:SHORTCUT); $s.TargetPath = $env:PYTHONW; $s.Arguments = ('"' + $env:SCRIPT + '"'); $s.WorkingDirectory = (Split-Path -Parent $env:SCRIPT); $s.Description = 'Affinity Discord Rich Presence'; $s.WindowStyle = 7; $s.Save()"
if errorlevel 1 (
    echo.
    echo Could not create the Windows startup shortcut.
    pause
    exit /b 1
)

echo.
echo Startup shortcut created. The script will start when you sign in to Windows.
echo Starting it now in the background...
start "" "%PYTHONW%" "%SCRIPT%"
echo.
echo Done! Keep Discord desktop running. Open an Affinity app to test it.
echo A log file will be saved as affinity_rpc.log in this folder.
timeout /t 5
endlocal
