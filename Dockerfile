FROM ubuntu:22.04
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update --fix-missing
RUN apt-get install -y libpq-dev gcc curl \
  build-essential python3-dev python3-pip python3-setuptools python3-wheel \
  python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
  libffi-dev shared-mime-info swig git imagemagick poppler-utils openssl libsqlite3-dev
RUN curl https://pyenv.run | bash
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/bin:$PATH
RUN pyenv install -v 3.8.18
RUN pyenv global 3.8.18
RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv install --dev --deploy
RUN pipenv install endesive==1.5.9
ADD . /app
