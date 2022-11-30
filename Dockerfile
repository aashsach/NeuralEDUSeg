FROM --platform=linux/amd64 python:3.6.15-bullseye
RUN apt-get update
RUN apt-get -y install gcc
RUN apt-get -y install nginx/bullseye
RUN apt-get -y install supervisor

COPY nginx.conf /etc/nginx/nginx.conf


WORKDIR neuraledu

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt --no-deps

COPY data data
COPY src src

WORKDIR src
COPY supervisord.conf supervisord.conf

HEALTHCHECK --start-period=150s CMD curl --fail http://localhost:8000/health || exit 1
CMD supervisord -c supervisord.conf