#!/bin/bash

set -e

if [[ "${ENV}" == "prod" ]]; then
  echo "You can't re-index the prod OpenSearch instance"
  exit 1
fi

python manage.py seedinternalusers
