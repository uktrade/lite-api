web: which swig; SWIG_LIB=/home/vcap/deps/0/apt/usr/share/swig4.0 CFLAGS=-I/home/vcap/deps/1/python/include/python3.9.18m pip3 install endesive==1.5.9 && python manage.py migrate && gunicorn --worker-class gevent -c api/conf/gconfig.py -b 0.0.0.0:$PORT api.conf.wsgi
celeryworker: celery -A api.conf worker -l info
celeryscheduler: celery -A api.conf beat
