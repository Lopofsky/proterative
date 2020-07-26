# pull official base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

# set work directory
WORKDIR /home/lopofsky/Custom-ies/quick_and_dirty/src/app/

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# copy requirements file
COPY ./requirements.txt /home/lopofsky/Custom-ies/quick_and_dirty/src/app/requirements.txt

# install dependencies
RUN set -eux \
    && apk add --no-cache --virtual .build-deps build-base \
        libressl-dev libffi-dev gcc musl-dev python3.8-dev \
        postgresql-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r /home/lopofsky/Custom-ies/quick_and_dirty/src/app/requirements.txt \
    && rm -rf /root/.cache/pip

# copy project
COPY ./app /home/lopofsky/Custom-ies/quick_and_dirty/src/app/