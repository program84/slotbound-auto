@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo [1/3] 安装 PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail

echo.
echo [2/3] 打包...
python -m PyInstaller --onefile --name slotbot --clean --noconfirm slotbot.py
if errorlevel 1 goto fail

echo.
echo [3/3] 复制运行所需文件到 dist\ ...
copy /y shot_decision.png dist\ >nul 2>nul
copy /y shot_skip.png     dist\ >nul 2>nul
copy /y shot_skull.png    dist\ >nul 2>nul

echo.
echo 完成：dist\slotbot.exe
echo 把 dist 里那个 exe 和三张 png 放在同一个文件夹就能用。
pause
exit /b 0

:fail
echo.
echo 打包失败，把上面的报错发出来。
pause
exit /b 1
