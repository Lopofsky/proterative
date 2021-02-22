#!/usr/bin/python3
# # -*- coding: utf-8 -*-
# SOURCE: https://github.com/encode/uvicorn/issues/706
import asyncio
loop = None

async def asgi_handler(scope, receiver, sender):
    global loop
    if scope['type'] == 'lifespan':
        message = await receiver()
        if message['type'] == 'lifespan.startup':
            loop = asyncio.get_running_loop()
            loop.create_task(cron())
            await sender({'type': 'lifespan.startup.complete'})
        elif message['type'] == 'lifespan.shutdown':
            #print("Shutdown received!")
            await sender({'type': 'lifespan.shutdown.complete'})
        return
    await sender({'type': 'http.response.start', 'status': 200, 'headers': [[b'content-type', b'text-plain']] })
    await sender({'type': 'http.response.body', 'body': b'fine test'})
    #print(f"Request to {scope['path']} complete")


async def cron():
    while True:
        #print("Cron tick")
        await asyncio.sleep(1)
    return None


if __name__ == '__main__':
    import uvicorn
    uvicorn.run("app.main:app",
                                host = '0.0.0.0',
                                port = 7000,
                                forwarded_allow_ips = "*",
                                lifespan = 'on',
                                workers = 4,
                                interface = 'asgi3',
                                timeout_keep_alive = 5)


'''
import uvicorn
if __name__ == "__main__":
        #allfiles = [f for f in listdir(getcwd())]
        uvicorn.run("app.main:app", host="0.0.0.0", port=7000, reload=True, log_level="info")
'''