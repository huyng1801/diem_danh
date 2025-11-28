@echo off
REM Setup Python 3.11+ venv for project
REM Change PYTHON_PATH below to your Python 3.11/3.12/3.14 executable if needed
set PYTHON_PATH=D:\Program Files\Python\Python311

REM Create venv in .venv folder
%PYTHON_PATH% -m venv .venv

REM Activate venv
call .venv\Scripts\activate

REM Upgrade pip & setuptools
python -m pip install --upgrade pip setuptools

REM Install requirements
pip install -r requirements.txt

REM Done
@echo Project venv setup complete. To activate later, run:
@echo   call .venv\Scripts\activate
