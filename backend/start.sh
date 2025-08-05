#!/bin/bash
source ../venv/bin/activate
pip install -r requirements.txt
python main.py &
echo "Backend started in background on http://localhost:8000"
echo "PID: $!"