@echo off
REM Windows batch script to set up virtual environment

echo Creating virtual environment...
python -m venv venv

echo.
echo Virtual environment created!
echo.
echo To activate the virtual environment, run:
echo   venv\Scripts\activate
echo.
echo Then install dependencies:
echo   pip install -r requirements.txt
echo.

pause

