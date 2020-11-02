## Running without docker

This describes how you can run the django app without docker but sill relies on
Docker Compose to provide services like the database, elasticsearch and redis

- Start a local Postgres/ES/redis stack: `docker-compose up -d redis db elasticsearch`
- Set up your local config file:
  - `cp local.env .env`
- Install pipenv:
  - `pip install pipenv`
  - `pipenv sync`
- Initialise submodules:
  - `git submodule init`
  - `git submodule update`
- Run the migrations: `pipenv run ./manage.py migrate`
- Build the elastic search index: `pipenv run ./manage.py search_index --rebuild -f`
- Run the application `pipenv run ./manage.py runserver 8100`
