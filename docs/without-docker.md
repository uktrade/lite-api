## Runing without docker
* Start a local Postgres: `docker run --name my-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`
* Set up your local config file:
  * `cp local.env .env`
  * If your local Postgres is not running with default options, edit the `DATABASE_URL` sections of `.env` file
* ensure you have installed pipenv on your environment
  * `pip install pipenv`
* Setup pipenv environment:
  * `pipenv sync`
* Initialise submodules
    * `git submodule init`
    * `git submodule update`
* Run the application: `pipenv run ./manage.py migrate && pipenv run ./manage.py runserver`