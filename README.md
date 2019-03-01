# lite-application-service
Service for managing applications and drafts in LITE.

## Running the service

* Download the repository:
  * `git clone https://github.com/uktrade/lite-application-service.git`
  * `cd lite-application-service` 
* Start a local Postgres: `docker run --name my-postgres -e POSTGRES_PASSWORD=password -p 5432:5432 -d postgres`
* Set up your local config file:
  * `cp conf/sample-application.conf conf/application.conf`
  * In service config options, replace `ENTER_USERNAME_HERE` and `ENTER_PASSWORD_HERE` values with their corresponding
    usernames and passwords from Vault.
  * If your local Redis and Postgres are not running with default options, edit the `db` and `redis` sections of the
    config file.
* Run the application: `sbt run`
* Go to the index page (e.g. `http://localhost:8000`)

## Endpoints

### Applications

Endpoint Group #1 description

**GET** `/applications/user/:id` - Returns a list of applications belonging to the specified user.

**POST** `/applications/user/:id` - Creates a new application belonging to the specified user.

### Drafts

Endpoint Group #2 description

**GET** `/drafts/user/:id` - Returns a list of drafts belonging to the specified user.

**POST** `/drafts/user/:id` - Creates a new draft belonging to the specified user.
