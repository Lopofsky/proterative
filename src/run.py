#!/usr/bin/python3
# # -*- coding: utf-8 -*-
# SOURCE: https://github.com/encode/uvicorn/issues/706
from os import getenv
from uvicorn import run
from platform import system
from dotenv import load_dotenv


if __name__ == "__main__":
    load_dotenv(dotenv_path='.env')
    workers = 1 if system() == "Windows" else 4
    async_loop = None if system() == "Windows" else "uvloop"
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0",
        "reload": True,
        "port": int(getenv('WEB_PORT', 8000)),
        "forwarded_allow_ips": "*",
        "lifespan": "on",
        "workers": workers,
        "interface": "asgi3",
        "timeout_keep_alive": 5,
        "proxy_headers": True,
    }
    if async_loop is not None:
        config["loop"] = "uvloop"
    
    run(**config)
