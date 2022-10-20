FROM python:3.10-slim-buster

ENV PYTHONUNBUFFERED=TRUE

# install essential packages
RUN apt-get update -y
RUN apt-get install -y git build-essential

# install & configure poetry
RUN python3 -m pip install poetry --no-cache-dir
RUN poetry config virtualenvs.in-project true

# make quake3-bot dir
RUN mkdir quake3-bot
WORKDIR /quake3-bot

# copy over bot/__main__.py so poetry can setup q3bot script while installing project
COPY bot/__main__.py bot/__main__.py

# install project
COPY pyproject.toml .
COPY poetry.lock .
RUN poetry install --no-dev --no-interaction

# copy over files
COPY bot bot

# run Villager Bot cluster
CMD poetry run q3bot
