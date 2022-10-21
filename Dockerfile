FROM python:3.6.15-slim-buster
RUN apt-get update
RUN apt-get -y install gcc

WORKDIR neuraledu

COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt --no-deps

COPY data data
COPY src src

WORKDIR src

CMD python segmenter_api.py