@echo off
echo ========================================
echo  EUFSI LCA Tool - Starting Backend
echo ========================================
echo.

cd backend

echo Activating virtual environment...
call venv\Scripts\activate

echo Starting backend server on http://localhost:8000...
python start.py
