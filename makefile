ARGUMENTS = $(filter-out $@,$(MAKECMDGOALS)) $(filter-out --,$(MAKEFLAGS))

docker-base = docker-compose -f docker-compose.e2e.yml

clean:
	-find . -type f -name "*.pyc" -delete
	-find . -type d -name "__pycache__" -delete

runserver:
	./manage.py runserver localhost:8100

migrate:
	./manage.py migrate

pip-runserver:
	pipenv run ./manage.py runserver localhost:8100

pip-migrate:
	pipenv run ./manage.py migrate

doc-migrate:
	docker exec -it api ./manage.py migrate

pip-manage:
	pipenv run ./manage.py $(ARGUMENTS)

manage:
	./manage.py $(ARGUMENTS)

pip-test:
	pipenv run ./manage.py test

test:
	./manage.py test

secrets:
	cp local.env .env

build-e2e:
	$(docker-base) build --build-arg GIT_ACCESS_CODE=${GIT_ACCESS_CODE}

start-e2e:
	$(docker-base) up

stop-e2e:
	$(docker-base) down --remove-orphans

seed:
	./manage.py seedrolepermissions
	./manage.py seedinternalusers
	./manage.py seedexporterusers
