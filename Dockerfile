FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir \
        "fastapi>=0.137,<1" \
        "jieba>=0.42,<1" \
        "langgraph>=1.2,<2" \
        "pydantic>=2.12,<3" \
        "python-dotenv>=1,<2" \
        "python-multipart>=0.0.20,<1" \
        "requests>=2.32,<3" \
        "streamlit>=1.58,<2" \
        "uvicorn>=0.49,<1"

COPY . .

EXPOSE 8000
EXPOSE 8501
