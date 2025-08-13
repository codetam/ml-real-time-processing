FROM python:3.10.14

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 libssl-dev git curl -y

WORKDIR /requirements

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /requirements

RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

WORKDIR /project/app
