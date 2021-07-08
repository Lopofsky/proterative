#!/usr/bin/python3
# # -*- coding: utf-8 -*-
# SOURCE: https://github.com/encode/uvicorn/issues/706
from uvicorn import run
from platform import system

if __name__ == '__main__':
    workers = 1 if system() == 'Windows' else 4
    async_loop = None if system() == 'Windows' else 'uvloop'
    if async_loop is None: run("app.main:app", host='0.0.0.0', reload=True, port=7000, forwarded_allow_ips="*", lifespan='on', workers=workers, interface='asgi3', timeout_keep_alive=5)
    else: run("app.main:app", host='0.0.0.0', reload=True, port=7000, forwarded_allow_ips="*", lifespan='on', workers=workers, interface='asgi3', loop='uvloop', timeout_keep_alive=5)
