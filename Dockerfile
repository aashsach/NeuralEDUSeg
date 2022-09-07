FROM python:3.6.15-slim-buster

WORKDIR nerualedu

COPY data data
COPY src src
COPY requirements.txt requirements.txt

RUN pip install -r requirements.txt

WORKDIR nerualedu/src

CMD python run.py