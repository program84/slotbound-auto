@echo off
cd /d "%~dp0"

echo [1/3] Installing PyInstaller...
python -m pip install --upgrade pyinstaller
if errorlevel 1 goto fail

echo.
echo [2/3] Building...
python -m PyInstaller --onefile --name slotbot --clean --noconfirm slotbot.py
if errorlevel 1 goto fail

echo.
echo [3/3] Copying runtime files into dist\ ...
copy /y shot_decision.png dist\ >nul 2>nul
copy /y shot_skip.png     dist\ >nul 2>nul
copy /y shot_skull.png    dist\ >nul 2>nul

echo.
echo Done: dist\slotbot.exe
echo Put the exe together with the three png files in one folder.
pause
exit /b 0

:fail
echo.
echo Build failed. See the messages above.
pause
exit /b 1
