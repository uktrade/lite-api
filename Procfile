web: python manage.py migrate && gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
celeryworker: celery -A api.conf worker -l info
celeryscheduler: celery -A api.conf beat
jobtest: python bin/copy_from_prod_s3.py
