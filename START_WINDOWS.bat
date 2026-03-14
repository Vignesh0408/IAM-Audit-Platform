@echo off
echo.
echo  InnaIT IAM Audit Platform
echo  --------------------------
echo  Installing dependencies...
pip install flask flask-cors gunicorn 2>nul
pip install flask flask-cors 2>nul
echo.
echo  Starting server...
echo  Open your browser at: http://127.0.0.1:5000
echo.
cd /d "%~dp0backend"
python app.py
pause
