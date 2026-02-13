FROM python:3.12-slim

RUN apt-get update && apt-get install -y curl

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN pip install --upgrade pip

COPY ./requirements.txt /app/requirements.txt
RUN pip install -r requirements.txt

COPY . /app

RUN chmod +x scripts/start_app.sh
RUN chmod +x scripts/start_outbox.sh
