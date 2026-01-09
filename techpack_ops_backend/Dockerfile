FROM python:3.11-slim

WORKDIR /APP

RUN pip install --no-cache-dir poetry

COPY pyproject.toml poetry.lock* ./

RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi --no-root --only main

COPY . .

EXPOSE 8000