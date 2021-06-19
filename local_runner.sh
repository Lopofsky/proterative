#!/bin/bash
cd $PWD/src
find $PWD -type d -name "__pycache__" | xargs rm -rf
find $PWD -type f -name ".pyc" | xargs rm -f

uvicorn app.main:app --reload --workers 4 --host 0.0.0.0 --port 7000