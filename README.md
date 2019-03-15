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
* Activate your Python virtual environment:
  * `cd venv`
  * `source bin/activate`
  * `cd ..`
* Run `pip install -r requirements.txt`
* Run the application: `python manage.py migrate && ./manage.py runserver`
* Go to the index page (e.g. `http://localhost:8000`)

## Endpoints

### Applications

Endpoint Group #1 description

**GET** `/applications/user/:id` - Returns a list of applications belonging to the specified user.

**POST** `/applications/user/:id` - Creates a new application belonging to the specified user.

### Drafts

Endpoint Group #2 description

**GET** `/drafts/:id` - Returns the specified draft.

**POST** `/drafts/:id` - Updates the specified draft with the data sent.

**GET** `/drafts/user/:id` - Returns a list of drafts belonging to the specified user.

**POST** `/drafts/user/:id` - Creates a new draft belonging to the specified user.


### Control Codes

Endpoint Group #2 description

**GET** `/control-codes/:id` - Returns the specified draft.

**POST** `/control-codes/:id` - Updates the specified draft with the data sent.

## Common Issues

`ModuleNotFoundError: No module named 'environ'` - Type `pip install -r requirements.txt`

## LITE Repositories

**[lite-api](https://github.com/uktrade/lite-api)** - Service for handling backend calls in LITE.

[lite-exporter-frontend](https://github.com/uktrade/lite-exporter-frontend) - Application for handling exporter related activity in LITE.

[lite-internal](https://github.com/uktrade/lite-internal-frontend) - Application for handling internal information in LITE.
