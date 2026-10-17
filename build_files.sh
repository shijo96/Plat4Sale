#!/bin/bash
echo "Building project assets for Plat4Sale..."
python3 -m pip install -r requirements.txt
python3 manage.py collectstatic --no-input --clear
echo "Build completed successfully!"
