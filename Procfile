web: file /layers/paketo-buildpacks_pipenv-install/packages/workspace-dqq3IVyd/bin/python && file src && file /usr/local/include && file /layers/paketo-buildpacks_pipenv-install/packages/workspace-dqq3IVyd/include && file /layers/paketo-buildpacks_cpython/cpython/include/python3.9 && SWIG_LIB=$(which swig) CFLAGS=-I$(which python) pip3 install endesive==1.5.9 && python manage.py migrate && gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
celeryworker: celery -A api.conf worker -l info
celeryscheduler: celery -A api.conf beat
