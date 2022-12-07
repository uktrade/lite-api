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
      which is 5462 (double check by viewing the docker-compose file) and change ELASTICSEARCH_HOST also

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
  - OR pull in the anonymised UAT data
    - install [cloudfoundry cli](https://docs.cloudfoundry.org/cf-cli/install-go-cli.html)
    - install [cloudfoundry conduit plugin](https://github.com/alphagov/paas-cf-conduit)
    - login to cloudfoundry `cf login --sso`
    - `cf conduit <UAT_PG_INSTANCE_NAME> -- docker run --rm -e PGUSER -e PGPASSWORD -e PGDATABASE -e PGPORT -e PGHOST=host.docker.internal postgres:12 pg_dump --no-acl --no-owner | docker-compose exec -T db psql -U postgres`

- Starting the service
  - `docker-compose up` - to start the API's django server
- Go to the index page (e.g. `http://localhost:8100`)
- At this point you might want to seed your database with some static
  - run `docker-compose run api ./manage.py seedall`

#### Git Hub pre-commit setup
- Install pre-commit (e.g MAC pip install pre-commit)
- pre-commit install

* to run on it's own
  - pre-commit run

If your changes incorrectly set off the pii/secrets warning, it can be added to `pii-secret-exclude.txt`

## Add a single user:


Run the following command to add new users (after setting INTERNAL_USERS and EXPORTER_USERS in .env):

```
./manage.py seedrolepermissions
./manage.py seedinternalusers
./manage.py seedexporterusers
```

to add subsequent new users

```
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' ./manage.py seedinternalusers
EXPORTER_USERS='[{"email"=>"foo@bar.com"}]' ./manage.py seedexporterusers
```

## Running Background tasks

We currently have two mechanisms for background tasks in lite;
- django-background-tasks: `pipenv run ./manage.py process_tasks` will run all background tasks
- celery: a celery container is running by default when using docker-compose.  If a working copy
    "on the metal" without docker, run celery with `watchmedo auto-restart -d . -R -p '*.py' -- celery -A api.conf worker -l info`

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

You'll need to install any dev [graphviz](https://graphviz.org/) dependencies (on ubuntu `sudo apt install libgraphviz-dev`) and then `pygraphviz`.

Gegenerate diagrams

    DJANGO_SETTINGS_MODULE=api.conf.settings_dev pipenv run ./manage.py create_er_diagrams

## Running Tests

- `pipenv run pytest`

## Running Code Coverage

- `pipenv pytest --cov=. --cov-report term --cov-config=.coveragerc`

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-frontend](https://github.com/uktrade/lite-frontend) - The web frontend for LITE.

## Running Bandit

`pipenv run bandit -r .`

## Adding new Control list entries

The control list entries are maintained in an excel sheet in an internal repo. They are arranged in a tree structure with each category in a different sheet. As with the changes in policy we need to update the list. This involves adding new entries, decontrolling existing entries or updating the description of entry(s).

To add a new entry simply add the description, rating at the correct level. Mark whether it is decontrolled or not by entering 'x' in the decontrolled column. Usually everything is controlled unless otherwise marked in this column.

If only description is to be updated then just edit the description text.

Once the changes are done run the seed command to populate the db with the updated entries and ensure no errors are reported.

`pipenv run ./manage.py seedcontrollistentries`

Deploy the API so that it picks up the updated entries in the corresponding environment. Because of the way the seeding commands are executed during deployment we have to deploy twice to see these changes. During deployment it first runs the seed commands and then deploys new changes so during the first deployment we are still seeding existing entries. If we deploy twice then the updated entries get seeded.

Once the API is deployed then restart the frontends because the control list entries are cached in the frontend and to discard them and pull updated list we need to restart the app.
