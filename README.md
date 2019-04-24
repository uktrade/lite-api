# lite-api

Service for handling backend calls in LITE.

## Running the service with docker

* Download the repository:
  * `git clone https://github.com/uktrade/lite-api.git`
  * `cd lite-api`

* First time setup
  * Set up your local config file:
    * `cp local.env .env`
  * Ensure docker is running
    * Build and start docker images:
    * `docker-compose build`
    * `docker-compose up`
  * Run the migrations
    * `./bin/migrate.sh`

* Starting the service
    * `docker-compose up`

* Go to the index page (e.g. `http://localhost:8100`)

***

## Runing without docker
* Start a local Postgres: `docker run --name my-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`
* Set up your local config file:
  * `cp local.env .env`
  * If your local Postgres is not running with default options, edit the `DATABASE_URL` sections of `.env` file
* ensure you have installed pipenv on your environment
  * `pip install pipenv`
* Setup pipenv environment:
  * `pipenv sync`
* Run the application: `pipenv run ./manage.py migrate && pipenv run ./manage.py runserver`

*** 

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-exporter-frontend](https://github.com/uktrade/lite-exporter-frontend) - Application for handling exporter related activity in LITE.

[lite-internal-frontend](https://github.com/uktrade/lite-internal-frontend) - Application for handling internal information in LITE.
