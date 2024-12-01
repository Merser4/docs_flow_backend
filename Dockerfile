FROM python:3.11-alpine

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

RUN poetry install --no-interaction --no-ansi

CMD ["poetry", "run", "python3", "./manage.py", "runserver", "0.0.0.0:8098"]