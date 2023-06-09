@echo off
:loop
echo Restarting server...
python app_async.py
timeout /t 1 >nul
goto loop

