web: CFLAGS=-I/home/vcap/deps/1/python/include/python3.7m pip3 install endesive==1.5.9 && python manage.py migrate && gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
worker: python manage.py process_tasks
celeryworker: celery -A api.conf worker -l info
