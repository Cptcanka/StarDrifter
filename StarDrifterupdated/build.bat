@echo off
REM Builds StarDrifter.exe into the dist\ folder.
python -m pip install -r requirements.txt
python -m PyInstaller --onefile --windowed --name StarDrifter star_drifter.py
echo.
echo Done! Your game is at dist\StarDrifter.exe
pause
