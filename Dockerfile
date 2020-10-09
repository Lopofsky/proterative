# pull official base image
FROM tiangolo/uvicorn-gunicorn-fastapi:python3.8

#ENV FLASK_APP run.py
# copy requirements file
COPY requirements.txt ./
COPY src/run.py ./
COPY src/app ./

# install dependencies
RUN /usr/local/bin/python -m pip install --upgrade pip || true
RUN pip install -r requirements.txt || true


EXPOSE 7000
CMD ["python",  "run.py"]
#CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "7000"]
