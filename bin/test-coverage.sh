#!/bin/bash
echo //////
echo Note: Run from the main app directory "bin/test-coverage.sh"
echo //////
pipenv run coverage run --source='.' manage.py test
pipenv run coverage report -m
pipenv run coverage html
open htmlcov/index.html