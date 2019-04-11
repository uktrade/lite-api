# lite-api

Service for handling backend calls in LITE.

## Running the service

* Download the repository:
  * `git clone https://github.com/uktrade/lite-api.git`
  * `cd lite-api`
* Start a local Postgres: `docker run --name my-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`
* Set up your local config file:
  * `cp local.env .env`
  * If your local Postgres is not running with default options, edit the `DATABASE_URL` sections of `.env` file
* Setup pipenv environment:
  * `pipenv sync`
* Run the application: `pipenv run ./manage.py migrate && pipenv run ./manage.py runserver`
* Go to the index page (e.g. `http://localhost:8000`)

## Endpoints

### Applications

Endpoints for creating and retrieving applications.

**GET** `/applications/` - Returns a list of applications.

**GET** `/applications/:id/` - Returns the specified application.

**POST** `/applications/` - Creates a new application from the _id_ provided in post data.

### Drafts

Endpoints for creating, updating and retrieving drafts.

**GET** `/drafts/` - Returns a list of drafts.

**GET** `/drafts/:id/` - Returns the specified draft.

**PUT** `/drafts/:id/` - Updates the specified draft with the data sent.

**DELETE** `/drafts/:id/` - Deletes the specified draft.

## Common Issues

`ModuleNotFoundError: No module named 'environ'` - Type `pip install -r requirements.txt`

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-exporter-frontend](https://github.com/uktrade/lite-exporter-frontend) - Application for handling exporter related activity in LITE.

[lite-internal-frontend](https://github.com/uktrade/lite-internal-frontend) - Application for handling internal information in LITE.
