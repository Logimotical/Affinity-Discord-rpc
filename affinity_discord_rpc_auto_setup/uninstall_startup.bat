@echo off
setlocal
set "SHORTCUT=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\Affinity Discord RPC.lnk"
if exist "%SHORTCUT%" (
    del "%SHORTCUT%"
    echo Removed Affinity Discord RPC from Windows startup.
) else (
    echo No startup shortcut was found.
)
echo.
echo This does not delete your Python script or log file.
pause
endlocal
