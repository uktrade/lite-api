![Logo](docs/logo.svg)

[![CircleCI](https://circleci.com/gh/uktrade/lite-api.svg?style=svg)](https://circleci.com/gh/uktrade/lite-api)
[![Maintainability](https://api.codeclimate.com/v1/badges/48bf94fd5e0e0abd617c/maintainability)](https://codeclimate.com/github/uktrade/lite-api/maintainability)

Service for handling backend calls in LITE.

## Before setup

- Clone the repository:
  - `git clone https://github.com/uktrade/lite-api.git`
  - `cd lite-api`

### A note on running the service without Docker

- Running the service with Docker is highly recommended.
- If running on native hardware locally (using your local `pipenv`), make sure to change the `DATABASE_URL` to use the port exposed by docker-compose
      which is `5462` (double check by viewing the `docker-compose` file) and also change `ELASTICSEARCH_HOST`
- More information is available in the docs at [without_docker.md](docs/without_docker.md).

## Running the service with Docker

- First time setup

  - Set up your local config file:

    - `cp local.env .env` - you will want to set this up with valid values, ask another developer or get them from Vault.
      If you want to run in Docker then uncomment the appropriate line in `.env` referring to `DATABASE_URL`.
    - In `.env`, also fill in the email field for `INTERNAL_USERS` and `EXPORTER_USERS` with valid values.

  - HAWK Authentication is enabled on API/Exporter/caseworker services by default. If you get issuing making any api calls i.e missing authentication / key    mismatch 
    - Check LITE_INTERNAL_HAWK_KEY ENV Keys match on API and caseworker
    - Check LITE_EXPORTER_HAWK_KEY ENV Keys match on  API and expoter

  - Initialise submodules

    - `git submodule init`
    - `git submodule update`

  - Ensure Docker Desktop (Docker daemon) is running

  - Build and start Docker images:

    - `docker network create lite` - shared network to allow API and frontend to communicate
    - `docker-compose build` - build the container image
    - `docker-compose up -d db` - to bring up the database to allow the migration to succeed

  - Once you have an empty database, you will need to run migrations.

  - Option 1:
    - `docker exec -it api /bin/bash` - open a shell session in api
    - `pipenv shell` - activate your pipenv environment
    - `./manage.py migrate` - perform the Django migrations (see `makefile` for convenience versions of this command)
    - (Known issue: by default Elasticsearch is enabled in the `.env` file and this can show a connection error at the end of the migration script. This can be safely ignored as the migration succeeding is not dependent on Elasticsearch running. Or you can disable Elasticsearch temporarily in the `.env` file if you prefer.)
  - Option 2:
    - Run the `make doc-migrate` command which does all of the above in one

- Starting the service for the first time
  - `docker-compose up` - to start the API's Django server
- Go to the caseworker home page (e.g. `http://localhost:8200`)
- If your database is empty (i.e. you just ran the migrations) then at this point you might want to seed your database with the static data
  - `docker exec -it api pipenv run ./manage.py seedall` - running with Docker
  - `pipenv run ./manage.py seedall` - without Docker

- Starting the service
  - In general you can use `docker-compose up --build` if you want to make sure new changes are included in the build

### Known issues when running with Docker

See [troubleshooting.md](docs/troubleshooting.md) in the docs for a list of current known issues.

## Git pre-commit setup

- Install pre-commit (see instructions here: https://pre-commit.com/#install)
- Run `pre-commit install` to activate pre-commit locally
- Run following to scan all files for issues
  - `pre-commit run --all-files`
- After this initial setup, pre-commit should run automatically whenever you run `git commit` locally.
- All developers must use the pre-commit hooks for the project. This is to make routine tasks easier (e.g. linting, style checking) and to help ensure secrets and personally identifiable information (PII) are not leaked.
- You should be able to use the project python environment to run pre-commit, but if the project python does not work for you, you should find a workaround for your dev environment (e.g. running a different higher python version just for pre-commit) or raise it with other developers. **Ignoring pre-commit errors is not an option.**

## Add a single user:


Run the following command from your api pipenv shell to initially add users (adds users defined in `INTERNAL_USERS` and `EXPORTER_USERS` in `.env`):

```
./manage.py seedrolepermissions
./manage.py seedinternalusers
./manage.py seedexporterusers
```

There is also the `make seed` command which does the same thing as the above. See the section Makefile commands below.

to add subsequent new users:

```
INTERNAL_USERS='[{"email"=>"foo@bar.gov.uk"}]' ./manage.py seedinternalusers
EXPORTER_USERS='[{"email"=>"foo@bar.com"}]' ./manage.py seedexporterusers
```

## Running background tasks

We currently have two mechanisms for background tasks in LITE;
- django-background-tasks: `pipenv run ./manage.py process_tasks` will run all background tasks
- celery: a celery container is running by default when using docker-compose.  If a working copy
    "on the metal" without docker, run celery with `watchmedo auto-restart -d . -R -p '*.py' -- celery -A api.conf worker -l info`
- celery-scheduler: a celery container is running by default when using docker-compose. This is to monitor any scheduled tasks  If a working copy
    "on the metal" without docker, run celery with `watchmedo auto-restart -d . -R -p '*.py' -- celery -A api.conf beat`

## Installing WeasyPrint for document generation

To produce PDF documents you will also need to install WeasyPrint. Do this after installing the python packages in the Pipfile;

> MacOS: https://weasyprint.readthedocs.io/en/stable/install.html#macos

> Linux: https://weasyprint.readthedocs.io/en/stable/install.html#debian-ubuntu

## Installing endesive for document signing

To digitally sign documents `endesive` requires the OS library `swig` to be installed. To install run `sudo apt-get install swig`

A `.p12` file is also required. Please see https://uktrade.atlassian.net/wiki/spaces/ILT/pages/1390870733/PDF+Document+Signing

## Documentation

**[API Docs available on GitHub Pages](https://uktrade.github.io/lite-api/)**

*For more docs on the development process and ongoing dev work, [check out LITE House Keeping.](https://github.com/uktrade/lite-house-keeping)*

[Running locally without Docker](docs/without_docker.md)

### Entity relationship diagrams

ER diagrams can be viewed in docs/entity-relation-diagrams/.

You'll need to install any dev [graphviz](https://graphviz.org/) dependencies (on ubuntu `sudo apt install libgraphviz-dev`) and then `pygraphviz`.

Gegenerate diagrams

    DJANGO_SETTINGS_MODULE=api.conf.settings_dev pipenv run ./manage.py create_er_diagrams

## Running tests

- `pipenv run pytest`

## Running code coverage

- `pipenv pytest --cov=. --cov-report term --cov-config=.coveragerc`

## LITE repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-frontend](https://github.com/uktrade/lite-frontend) - The web frontend for LITE.

## Running bandit

`pipenv run bandit -r .`

## Adding new control list entries

The control list entries are maintained in an Excel sheet in an internal repo. They are arranged in a tree structure with each category in a different sheet. As with the changes in policy we need to update the list. This involves adding new entries, decontrolling existing entries or updating the description of entries.

To add a new entry simply add the description, rating at the correct level. Mark whether it is decontrolled or not by entering 'x' in the decontrolled column. Usually everything is controlled unless otherwise marked in this column.

If only description is to be updated then just edit the description text.

Once the changes are done run the seed command to populate the database with the updated entries and ensure no errors are reported.

`pipenv run ./manage.py seedcontrollistentries`

Deploy the API so that it picks up the updated entries in the corresponding environment. Because of the way the seeding commands are executed during deployment we have to deploy twice to see these changes. During deployment it first runs the seed commands and then deploys new changes so during the first deployment we are still seeding existing entries. If we deploy twice then the updated entries get seeded.

Once the API is deployed then restart the frontends because the control list entries are cached in the frontend and to discard them and pull the updated list we need to restart the app.

## Makefile commands

The `makefile` in the top-level directory is where frequently used shell commands can be stored for convenience. For example, running the command:

```sh
make seed
```

is equivalent to

```sh
./manage.py seedrolepermissions
./manage.py seedinternalusers
./manage.py seedexporterusers
```

but is more convenient to use. This is helpful to have when doing things like tearing down and setting up the database multiple times per day.

The commands should be self-documenting with a name that clearly describes what the command does.
