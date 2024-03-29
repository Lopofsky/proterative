# pull official base image
FROM python:3.8

# copy requirements file & qnd src
COPY src/ ./

# install dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip || true
RUN pip install -r requirements.txt || true

ARG POSTGRES_USER
ENV POSTGRES_USER=$POSTGRES_USER
ARG POSTGRES_PASSWORD
ENV POSTGRES_PASSWORD=$POSTGRES_PASSWORD
ARG POSTGRES_SERVER
ENV POSTGRES_SERVER=$POSTGRES_SERVER
ARG POSTGRES_DB
ENV POSTGRES_DB=$POSTGRES_DB
ARG POSTGRES_PORT
ENV POSTGRES_PORT=$POSTGRES_PORT
ARG EXTRA_DBS
ENV EXTRA_DBS=$EXTRA_DBS
ARG SESSION_SECRET
ENV SESSION_SECRET=$SESSION_SECRET
ARG DO_YOU_WANT_USERS
ENV DO_YOU_WANT_USERS=$DO_YOU_WANT_USERS
ARG WHERE_AM_I
ENV WHERE_AM_I=$WHERE_AM_I
# SSL
ARG FORWARDED_ALLOW_IPS
ENV FORWARDED_ALLOW_IPS=$FORWARDED_ALLOW_IPS
ARG SSL_CERTIFICATE
ENV SSL_CERTIFICATE=$SSL_CERTIFICATE
ARG SSL_KEYFILE
ENV SSL_KEYFILE=$SSL_KEYFILE
ARG UPLOADS_PATH
ENV UPLOADS_PATH=$UPLOADS_PATH

RUN echo "$SSL_CERTIFICATE"

EXPOSE 7000
# https://oprearocks.medium.com/how-to-properly-override-the-entrypoint-using-docker-run-2e081e5feb9d
#CMD ["uvicorn", "app.main:app", "--forwarded-allow-ips", "*", "--proxy-headers", "--reload", "--workers", "4", "--interface", "asgi3", "--host", "0.0.0.0", "--port", "7000"]
CMD ["python", "run.py"]