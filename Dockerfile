# pull official base image
FROM python:3.8

#ENV FLASK_APP run.py
# copy requirements file
COPY requirements.txt ./
#COPY src/run.py ./
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

EXPOSE 7000
#CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "7000"]
CMD ["uvicorn", "app.main:app", "--reload", "--workers", "4", "--host", "0.0.0.0", "--port", "7000"]
