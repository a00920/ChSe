#!/bin/bash

# Start Gunicorn processes
if [ "$ENV" = "production" ]
then
    echo Starting Gunicorn.
    exec gunicorn wsgi:application --bind 0.0.0.0:8000 --workers 4 --reload --timeout 3000
else
    echo Starting Django dev server
    python manage.py runserver 0.0.0.0:8000
fi
