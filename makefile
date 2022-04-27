ARGUMENTS = $(filter-out $@,$(MAKECMDGOALS)) $(filter-out --,$(MAKEFLAGS))

docker-base = docker-compose -f docker-compose.e2e.yml

clean:
	-find . -type f -name "*.pyc" -delete
	-find . -type d -name "__pycache__" -delete

runserver:
	pipenv run ./manage.py runserver localhost:8100

migrate:
	pipenv run ./manage.py migrate

manage:
	pipenv run ./manage.py $(ARGUMENTS)

test:
	pipenv run ./manage.py test

secrets:
	cp local.env .env

build-e2e:
	$(docker-base) build --build-arg GIT_ACCESS_CODE=${GIT_ACCESS_CODE}

start-e2e:
	$(docker-base) up

stop-e2e:
	$(docker-base) down --remove-orphans
