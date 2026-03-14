#!/bin/bash
echo ""
echo "  InnaIT IAM Audit Platform"
echo "  --------------------------"
echo "  Installing dependencies..."
pip3 install flask flask-cors --quiet 2>/dev/null || pip install flask flask-cors --quiet
echo ""
echo "  Starting server..."
echo "  Open your browser at: http://127.0.0.1:5000"
echo ""
cd "$(dirname "$0")/backend"
python3 app.py
