ARGUMENTS = $(filter-out $@,$(MAKECMDGOALS)) $(filter-out --,$(MAKEFLAGS))

docker-base = docker-compose -f docker-compose.e2e.yml

build-e2e:
	$(docker-base) build --build-arg GIT_ACCESS_CODE=${GIT_ACCESS_CODE}

clean:
	-find . -type f -name "*.pyc" -delete
	-find . -type d -name "__pycache__" -delete

doc-manage:
	docker exec -it api pipenv run ./manage.py $(ARGUMENTS)

doc-migrate:
	docker exec -it api pipenv run ./manage.py migrate

doc-runserver:
	docker exec -it api pipenv run ./manage.py runserver localhost:8100

doc-seed:
	docker exec -it api pipenv run ./manage.py seedrolepermissions
	docker exec -it api pipenv run ./manage.py seedinternalusers
	docker exec -it api pipenv run ./manage.py seedexporterusers

doc-test:
	docker exec -it api pipenv run ./manage.py test

manage:
	./manage.py $(ARGUMENTS)

migrate:
	./manage.py migrate

pip-manage:
	pipenv run ./manage.py $(ARGUMENTS)

pip-migrate:
	pipenv run ./manage.py migrate

pip-runserver:
	pipenv run ./manage.py runserver localhost:8100

pip-seed:
	pipenv run ./manage.py seedrolepermissions
	pipenv run ./manage.py seedinternalusers
	pipenv run ./manage.py seedexporterusers

pip-test:
	pipenv run ./manage.py test

runserver:
	./manage.py runserver localhost:8100

secrets:
	cp local.env .env

seed:
	./manage.py seedrolepermissions
	./manage.py seedinternalusers
	./manage.py seedexporterusers

start-e2e:
	$(docker-base) up

stop-e2e:
	$(docker-base) down --remove-orphans

test:
	./manage.py test
