FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir -r requirements.txt

RUN groupadd --system crawler \
    && useradd \
        --system \
        --gid crawler \
        --home-dir /app \
        --shell /usr/sbin/nologin \
        crawler

COPY --chown=crawler:crawler . .

USER crawler
