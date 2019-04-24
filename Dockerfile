FROM python:3.7-slim
MAINTAINER tools@digital.trade.gov.uk
WORKDIR /app
RUN pip3 install pipenv
ADD Pipfile* /app/
RUN pipenv sync
ADD . /app
