![Logo](docs/logo.svg)

[![CircleCI](https://circleci.com/gh/uktrade/lite-api.svg?style=svg)](https://circleci.com/gh/uktrade/lite-api)
[![Maintainability](https://api.codeclimate.com/v1/badges/48bf94fd5e0e0abd617c/maintainability)](https://codeclimate.com/github/uktrade/lite-api/maintainability)

Service for handling backend calls in LITE.

## Before setup

- Clone the repository:
  - `git clone https://github.com/uktrade/lite-api.git`
  - `cd lite-api`
  - Install [Homebrew](https://brew.sh/)

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

  - Ensure Docker Desktop (Docker Daemon) is running

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
  - Option 3:
    - Run `docker-compose up` to start the API's Django server
    - Run the `make first-run` command which will run the migrations, seedall and populate the database with test data

- Starting the service for the first time
  - `docker-compose up` - to start the API's Django server
- Go to the caseworker home page (e.g. `http://localhost:8200`)
Unless you chose Option 3 which already seeded and populated the database, you will now need to do this manually.
- If your database is empty (i.e. you just ran the migrations) then at this point you might want to seed your database with the static data (such as users, teams and countries)
  - `docker exec -it api pipenv run ./manage.py seedall` - running with Docker
  - `pipenv run ./manage.py seedall` - without Docker
- You'll also want to populate the db with some test licence application data
  - `docker exec -it api pipenv run ./manage.py create_test_data 10` - running with Docker
  - `pipenv run ./manage.py create_test_data 10` - without Docker
  - This command looks for and requires the following user `{user = {"first_name": "TAU","last_name": "User","email": "tautest@example.com"}}`. If it errors due to not finding the user then seed them into the database - see [Add a single user](#add-a-single-user)
  - It also requires the ENV variables to be set to `localhost`

- Starting the service
  - In general you can use `docker-compose up --build` if you want to make sure new changes are included in the build
- Indexing search
  - If this is something you require, you can run `make rebuild-search` to rebuild the search indexes using your local db.

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
We currently use celery for async tasks and scheduling in LITE;
- celery: a celery container is running by default when using docker-compose.  If a working copy
    "on the metal" without docker, run celery with `watchmedo auto-restart -d . -R -p '*.py' -- celery -A api.conf worker -l info`
- celery-scheduler: a celery container is running by default when using docker-compose. This is to monitor any scheduled tasks  If a working copy
    "on the metal" without docker, run celery with `watchmedo auto-restart -d . -R -p '*.py' -- celery -A api.conf beat`

## Installing WeasyPrint for document generation

To produce PDF documents you will also need to install WeasyPrint. Do this after installing the python packages in the Pipfile;

> MacOS: `brew install weasyprint`

> Linux: https://weasyprint.readthedocs.io/en/stable/install.html#debian-ubuntu

## Installing endesive for document signing

To digitally sign documents `endesive` requires the OS library `swig` to be installed. To install run `brew install swig`

A `.p12` file is also required. Please see https://uktrade.atlassian.net/wiki/spaces/ILT/pages/1390870733/PDF+Document+Signing

## Documentation

**[API Docs available on GitHub Pages](https://uktrade.github.io/lite-api/)**

*For more docs on the development process and ongoing dev work, [check out LITE House Keeping.](https://github.com/uktrade/lite-house-keeping)*

[Running locally without Docker](docs/without_docker.md)

### Entity relationship diagrams

ER diagrams can be viewed in docs/entity-relation-diagrams/.

You'll need to install any dev [graphviz](https://graphviz.org/) dependencies (on ubuntu `sudo apt install libgraphviz-dev`) and then `pygraphviz`.
  ```
  brew install graphviz
  pip install pygraphviz
  ```

Gegenerate diagrams

    DJANGO_SETTINGS_MODULE=api.conf.settings_dev pipenv run ./manage.py create_er_diagrams

## Running tests

Locally
- `pipenv run pytest`
- `pipenv run pytest --reuse-db` to speed up tests

In Docker
- Running `docker exec -it api pipenv run pytest` or run `pipenv run pytest` in Docker Desktop with any desired flags

## Running code coverage

- `pipenv pytest --cov=. --cov-report term --cov-config=.coveragerc`

## LITE repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-frontend](https://github.com/uktrade/lite-frontend) - The web frontend for LITE.

## Running bandit

`pipenv run bandit -r .`

## Control list entries cache

We have a 24 hour cache for CLEs on the frontend.

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
