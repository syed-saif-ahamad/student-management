#!/bin/bash

# Install Python dependencies
pip install -r requirements.txt

# Collect static files for WhiteNoise
python manage.py collectstatic --noinput

# Run database migrations on Neon Postgres
python manage.py migrate --noinput
