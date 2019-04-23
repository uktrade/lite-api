FROM python:3.7-slim
MAINTAINER tools@digital.trade.gov.uk
WORKDIR /app
ADD requirements*.txt /app/
RUN pip3 install -r requirements.txt
ADD . /app