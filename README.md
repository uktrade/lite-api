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

## Documentation

**[API Docs available on GitHub Pages](https://uktrade.github.io/lite-api/)**

[Running locally without Docker](docs/without-docker.md)

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-exporter-frontend](https://github.com/uktrade/lite-exporter-frontend) - Application for handling exporter related activity in LITE.

[lite-internal-frontend](https://github.com/uktrade/lite-internal-frontend) - Application for handling internal information in LITE.
