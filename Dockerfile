FROM python:3.12.2-slim-bullseye

ENV PYTHONUNBUFFERED 1
ENV PYTHONDONTWRITEBYTECODE 1
ENV PIP_DISABLE_PIP_VERSION_CHECK 1

ENV ENVIRONMENT "production"

WORKDIR /app

COPY poetry.lock pyproject.toml /app/

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev


COPY . /app/

WORKDIR /app/project

RUN python manage.py migrate

CMD ["gunicorn", "project.wsgi:application", "--bind", "0.0.0.0:8000"]
