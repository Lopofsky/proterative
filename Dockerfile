# pull official base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

#ENV FLASK_APP run.py
# copy requirements file
COPY requirements.txt .env ./
COPY src/app app

# install dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip || true
RUN pip install -r requirements.txt || true


EXPOSE 8000

CMD ["uvicorn",  "app.main:app", "--reload", "--workers", "4", "--host", "127.0.0.1", "--port", "8000"]
