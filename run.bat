@echo off
echo ======================================================================
echo           INTELLIGENT HEALTHCARE RECOMMENDATION SYSTEM (CDSS)
echo ======================================================================
echo 1. Initializing and Seeding SQLite Relational Database...
python database/db_manager.py

echo 2. Testing Data Mining ML Engine...
python ml_engine/data_mining.py

echo 3. Launching Flask Web Server...
echo Dashboard will be available at: http://127.0.0.1:5000
start "" "http://127.0.0.1:5000"
python app.py
pause
