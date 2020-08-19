web: pip3 install endesive && python manage.py migrate && gunicorn --worker-class gevent --preload -c conf/gconfig.py -b 0.0.0.0:$PORT conf.wsgi
worker: python manage.py process_tasks
