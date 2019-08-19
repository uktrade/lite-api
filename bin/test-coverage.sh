#!/bin/bash
echo //////
echo Note: Run from the main app directory "bin/test-coverage.sh"
echo //////
pipenv run coverage run manage.py test
pipenv run coverage html
open htmlcov/index.html
