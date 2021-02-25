#!/usr/bin/python3
# # -*- coding: utf-8 -*-
# SOURCE: https://github.com/encode/uvicorn/issues/706
import uvicorn, platform

if __name__ == '__main__':
    workers = 1 if platform.system() == 'Windows' else 4
    uvicorn.run("app.main:app", host='0.0.0.0', reload=True, port=7000, forwarded_allow_ips="*", lifespan='on', workers=workers, interface='asgi3', timeout_keep_alive=5)
