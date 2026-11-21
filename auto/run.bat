@echo off
chcp 65001 >nul
cd /d "%~dp0"

set "PY="
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY where py >nul 2>nul && set "PY=py"

if not defined PY (
    echo.
    echo 没有找到 Python。
    echo 请先安装 https://www.python.org/downloads/
    echo 安装时记得勾选 "Add python.exe to PATH"。
    echo.
    pause
    exit /b 1
)

%PY% -c "import numpy, PIL" >nul 2>nul
if errorlevel 1 (
    echo 首次运行，正在安装依赖，请稍候...
    %PY% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo.
        echo 依赖安装失败，把上面的报错发出来。
        pause
        exit /b 1
    )
)

%PY% slotbot.py %*
if errorlevel 1 pause
