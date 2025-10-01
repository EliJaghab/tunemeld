#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Collect static files for Django
python backend/manage.py collectstatic --noinput

# Run Django migrations
python backend/manage.py migrate --noinput