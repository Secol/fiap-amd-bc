FROM python:3.12

ADD requirements.txt /app/requirements.txt
WORKDIR /app


RUN pip install -r requirements.txt