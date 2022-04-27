#!/bin/bash -xe
python /app/manage.py migrate --noinput

# Load initial data
python /app/manage.py seedall

# Create initial users
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' /app/manage.py seedinternalusers
EXPORTER_USERS='[{"email"=>"foo@bar.com"}]' /app/manage.py seedexporterusers

# Rebuild ES index
LITE_API_ENABLE_ES=true /app/manage.py search_index --rebuild -f

# Run app
python /app/manage.py runserver 0.0.0.0:8100
