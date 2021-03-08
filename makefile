ARGUMENTS = $(filter-out $@,$(MAKECMDGOALS)) $(filter-out --,$(MAKEFLAGS))

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
