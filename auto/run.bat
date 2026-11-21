@echo off
cd /d "%~dp0"

set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY call :findpy python
if not defined PY call :findpy py
if not defined PY goto nopy

%PY% -c "import numpy, PIL" >nul 2>nul
if not errorlevel 1 goto run

echo.
echo First run: installing dependencies, please wait...
echo.
%PY% -m pip install -r requirements.txt
if errorlevel 1 goto deperr

:run
%PY% slotbot.py %*
if errorlevel 1 pause
exit /b 0

:findpy
where %1 >nul 2>nul
if errorlevel 1 exit /b 0
set "PY=%1"
exit /b 0

:nopy
echo.
echo Python not found on this computer.
echo Install Python 3.10+ from https://www.python.org/downloads/
echo During install, tick "Add python.exe to PATH".
echo.
pause
exit /b 1

:deperr
echo.
echo Dependency install failed. See the messages above.
pause
exit /b 1
