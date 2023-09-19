FROM python:3.8.17-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update --fix-missing
RUN apt-get install -y libpq-dev gcc \
  build-essential python3-dev python3-pip python3-setuptools python3-wheel \
  python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
  libffi-dev shared-mime-info swig git imagemagick poppler-utils
RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv install --dev --system --deploy
RUN pip3 install endesive==1.5.9
ADD . /app
