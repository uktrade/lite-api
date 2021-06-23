![Logo](docs/logo.svg)

[![CircleCI](https://circleci.com/gh/uktrade/lite-api.svg?style=svg)](https://circleci.com/gh/uktrade/lite-api)
[![Maintainability](https://api.codeclimate.com/v1/badges/48bf94fd5e0e0abd617c/maintainability)](https://codeclimate.com/github/uktrade/lite-api/maintainability)

Service for handling backend calls in LITE.

## Running the service with docker

- Download the repository:
  - `git clone https://github.com/uktrade/lite-api.git`
  - `cd lite-api`
- First time setup

  - Set up your local config file:

    - `cp local.env .env` - you will want to set this up with valid values, ask another developer or get them from Vault.
      If you want to run in Docker then uncomment the appropriate line in `.env` referring to DATABASE_URL. 
    - In `.env`, also fill in the email field for INTERNAL_USERS and EXPORTER_USERS with valid values.
    - If running locally (using pipenv), make sure to change the DATABASE_URL to use the port exposed by docker-compose
      which is 5462 (double check by viewing the docker-compose file)

  - Initialise submodules

    - `git submodule init`
    - `git submodule update`

  - Ensure docker is running

  - Build and start docker images:

    - `docker network create lite` - shared network to allow API and frontend to communicate
    - `docker-compose build` - build the container image
    - `docker-compose up -d db` - to bring up the db to allow the migrate to succeed

  - Run the migrations
    - `./bin/migrate.sh` - Perform the Django migrations

- Starting the service
  - `docker-compose up` - to start the API's django server
- Go to the index page (e.g. `http://localhost:8100`)
- At this point you might want to seed your database with some static
  - run `docker-compose run api ./manage.py seedall`

## Add a single user:

Run the following command to add new users:

```
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' ./manage.py seedinternalusers
EXPORTER_USERS='[{"email"=>"foo@bar.com"}]' ./manage.py seedexporterusers
```

## Running Background tasks

`pipenv run ./manage.py process_tasks` will run all background tasks

## Installing WeasyPrint for document generation

To produce PDF documents you will also need to install WeasyPrint.
Do this after installing the python packages in the Pipfile;

> MacOS: https://weasyprint.readthedocs.io/en/stable/install.html#macos

> Linux: https://weasyprint.readthedocs.io/en/stable/install.html#debian-ubuntu

## Installing endesive for document signing

To digitally sign documents `endsesive` requires the OS library swig to be installed.
To install run `sudo apt-get install swig`

A p12 file is also required. Please see https://uktrade.atlassian.net/wiki/spaces/ILT/pages/1390870733/PDF+Document+Signing

## Documentation

**[API Docs available on GitHub Pages](https://uktrade.github.io/lite-api/)**

[Running locally without Docker](docs/without_docker.md)

### Entity Relationship diagrams

ER Diagrams can be viewed in docs/entity-relation-diagrams/.

To regenerate the diagrams run `pipenv run ./manage.py create_er_diagrams`

## Running Tests

- `pipenv run ./manage.py test` will run all tests (takes over 30 minutes)
- `pipenv run ./manage.py test --parallel` will run all tests in parallel
- `pipenv run ./manage.py test api/cases` will run the `cases` module tests

## Running Code Coverage

- `pipenv run ./manage.py coverage <module_to_run_coverage_on> <tests_to_run>`

1. Providing no positional arguments implies that you want to run all tests and collect the coverage:
   - `pipenv run ./manage.py coverage`
2. The first positional argument implies what module you want to collect coverage for:
   - `pipenv run ./manage.py coverage cases` will collect coverage on the `cases` module and run only the `cases` tests
3. The second positional argument implies what tests to run in order to collect coverage for the given module:
   - `pipenv run ./manage.py coverage cases all` will collect coverage on the `cases` module and run all tests
   - `pipenv run ./manage.py coverage cases queues` will collect coverage on the `cases` module and only run the `queues` tests

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-frontend](https://github.com/uktrade/lite-frontend) - The web frontend for LITE.

## Running Bandit

`pipenv run bandit -r .`
