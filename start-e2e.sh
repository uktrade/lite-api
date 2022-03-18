#!/bin/bash -xe
python /app/manage.py migrate --noinput

# Load initial data
python /app/manage.py seedall

# Create initial users
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' /app/manage.py seedinternalusers
EXPORTER_USERS='[{"email"=>"foo@bar.com"}]' /app/manage.py seedexporterusers

# Run background tasks
python /app/manage.py process_tasks

# Run runserver in a while loop as the whole docker container will otherwise die
# when there is bad syntax
while true; do
    python /app/manage.py runserver_plus 0.0.0.0:8100
    sleep 1
done
