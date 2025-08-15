# =======================
# Stage 1: Base stage
# =======================
FROM python:3.10.14-slim as base

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg libsm6 libxext6 libssl-dev git curl \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /requirements

COPY requirements.txt /requirements
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

WORKDIR /project


# =======================
# Stage 2: Production stage
# =======================
FROM base as prod

COPY app/ .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]


# =======================
# Stage 3: Development stage
# =======================
FROM base as dev
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
