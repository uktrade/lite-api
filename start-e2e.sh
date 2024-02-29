#!/bin/bash -xe
cd /app/
pipenv run ./manage.py migrate --noinput

pipenv run ./manage.py seedall

# Create initial users
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' pipenv run ./manage.py seedinternalusers

# Fill sanctions in ES
LITE_API_ENABLE_ES=true pipenv run ./manage.py ingest_ui_test_sanctions

# Rebuild ES index
LITE_API_ENABLE_ES=true pipenv run ./manage.py search_index --rebuild -f

# Run app
pipenv run ./manage.py runserver 0.0.0.0:8100
