# lite-api

[![CircleCI](https://circleci.com/gh/uktrade/lite-api.svg?style=svg)](https://circleci.com/gh/uktrade/lite-api)
[![Maintainability](https://api.codeclimate.com/v1/badges/48bf94fd5e0e0abd617c/maintainability)](https://codeclimate.com/github/uktrade/lite-api/maintainability)

Service for handling backend calls in LITE.

## Running the service with docker

* Download the repository:
  * `git clone https://github.com/uktrade/lite-api.git`
  * `cd lite-api`
* First time setup
  * Set up your local config file:
    * `cp docker.env .env`
  * Initialise submodules
    * `git submodule init`
    * `git submodule update`
  * Ensure docker is running
    * Build and start docker images:
    * `docker-compose build` - build the container image
    * `docker-compose up`  - to bring up the db and the api service to allow the migrate to succeed
  * Run the migrations
    * `./bin/migrate.sh` - Perform the Django migrations
* Starting the service
    * `docker-compose up`
* Go to the index page (e.g. `http://localhost:8100`)

## Installing WeasyPrint for document generation
To produce PDF documents you will also need to install WeasyPrint. 
Do this after installing the python packages in the Pipfile;

> MacOS: https://weasyprint.readthedocs.io/en/stable/install.html#macos

> Linux: https://weasyprint.readthedocs.io/en/stable/install.html#debian-ubuntu

## Documentation

**[API Docs available on GitHub Pages](https://uktrade.github.io/lite-api/)**

[Running locally without Docker](docs/without_docker.md)

## Running Tests

- `pipenv run ./manage.py test` will run all tests
- `pipenv run ./manage.py test cases` will run the `cases` module tests

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

[lite-exporter-frontend](https://github.com/uktrade/lite-exporter-frontend) - Application for handling exporter related activity in LITE.

[lite-internal-frontend](https://github.com/uktrade/lite-internal-frontend) - Application for handling internal information in LITE.


## Running Bandit

`pipenv run bandit -r .`


## Running API tests

`pipenv run ./manage.py test`

with option `--parallel` to run them in parallel

To run a specific folder:

`pipenv run ./manage.py test <folder_name>`
