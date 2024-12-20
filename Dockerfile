FROM ubuntu:22.04
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /app
RUN apt-get update --fix-missing
RUN apt-get install -y curl build-essential
RUN curl --fail https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add
RUN sh -c 'echo "deb https://apt.postgresql.org/pub/repos/apt jammy-pgdg main" > /etc/apt/sources.list.d/pgdg.list'
RUN apt-get update
RUN apt-get install -y libpq-dev gcc \
  build-essential python3-dev python3-pip python3-setuptools python3-wheel \
  python3-cffi libcairo2 libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0 \
  libffi-dev shared-mime-info swig git imagemagick poppler-utils openssl \
  libsqlite3-dev graphviz graphviz-dev postgresql-client-12
RUN curl https://pyenv.run | bash
ENV HOME /root
ENV PYENV_ROOT $HOME/.pyenv
ENV PATH $PYENV_ROOT/bin:$PATH
RUN pyenv install -v 3.9.18
RUN pyenv global 3.9.18
RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv install --dev --deploy
RUN pipenv install endesive==1.5.9
ADD . /app
