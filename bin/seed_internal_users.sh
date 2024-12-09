#!/bin/bash

set -e

if [[ "${ENV}" == "prod" ]]; then
  echo "You can't seed users on prod"
  exit 1
fi

python manage.py seedinternalusers
