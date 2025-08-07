#!/bin/bash
source ../venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py &
echo "Backend started in background on http://localhost:8000"
echo "PID: $!"