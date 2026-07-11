FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY . .

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -e .

EXPOSE 8000
EXPOSE 8501
