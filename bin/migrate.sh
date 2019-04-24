#!/bin/bash
docker-compose run api pipenv run ./manage.py migrate
