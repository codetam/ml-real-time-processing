# =======================
# Stage 1: Build stage
# =======================
FROM python:3.10.14 as base

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6 libssl-dev git curl -y

WORKDIR /requirements

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

COPY requirements.txt /requirements

RUN pip3 install --no-cache-dir --upgrade pip && \
    pip3 install --no-cache-dir -r requirements.txt

WORKDIR /project/app

# =======================
# Stage 2: Production stage
# =======================
FROM base AS prod

COPY app/ .

CMD ["python", "main.py"]

# =======================
# Stage 3: Development stage
# =======================
FROM base AS dev

CMD ["python", "main.py"]