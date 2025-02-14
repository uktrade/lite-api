web-dbt-platform: python manage.py migrate && gunicorn -c api/conf/gconfig-dbt-platform.py -b 0.0.0.0:$PORT api.conf.wsgi
dump-and-anonymise: python manage.py dump_and_anonymise
rebuild-search-index: python manage.py search_index --rebuild -f
seed-internal-users: ./bin/seed_internal_users.sh
celeryworker: celery -A api.conf worker -l info
celeryscheduler: celery -A api.conf beat
