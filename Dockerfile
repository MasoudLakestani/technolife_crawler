FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry lock && \
    poetry install --no-root

COPY technolife/ ./technolife/

WORKDIR /app/technolife


CMD ["scrapy", "crawl", "technolifeProduct"]