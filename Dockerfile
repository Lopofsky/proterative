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
ARG SESSION_SECRET
ENV SESSION_SECRET=$SESSION_SECRET
ARG DO_YOU_WANT_USERS
ENV DO_YOU_WANT_USERS=$DO_YOU_WANT_USERS
ARG WHERE_AM_I
ENV WHERE_AM_I=$WHERE_AM_I

# Set to the port that your webapp listens on
ENV VIRTUAL_PORT=7000
# Can be comma-separated lis
ENV VIRTUAL_HOST=test.plushotels.gr
# The domain for the cert, can also be comma-separated
ENV LETSENCRYPT_HOST=test.plushotels.gr
# Your email for the cert
ENV LETSENCRYPT_EMAIL=test.plushotels.gr
# 192.168.1.88
EXPOSE 7000
#CMD ["whereis", "uvicorn"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000" "--reload"]
CMD ["uvicorn", "app.main:app", "--reload", "--workers", "4", "--host", "0.0.0.0", "--port", "7000"]
