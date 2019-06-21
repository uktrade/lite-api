## Runing without docker

* Start a local Postgres: `docker run --name lite-api -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`
* Set up your local config file:
  * `cp local.env .env`
* Install pipenv:
  * `pip install pipenv`
  * `pipenv sync`
* Initialise submodules:
    * `git submodule init`
    * `git submodule update`
* Run the application: `pipenv run ./manage.py migrate && pipenv run ./manage.py runserver 8100`
