FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN pip install poetry

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY . .

RUN poetry config virtualenvs.create false
RUN poetry install --no-interaction --no-ansi --no-root

RUN python manage.py migrate