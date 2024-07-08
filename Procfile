web1: SWIG_LIB=$(which swig) CFLAGS=-I$(which python) pip3 install endesive==1.5.9 && python manage.py migrate && gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
celeryworker: celery -A api.conf worker -l info
celeryscheduler: celery -A api.conf beat
web: gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
