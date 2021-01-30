# Fast-Api doesn't have (hopefully yet) server-side support for sessions: https://github.com/tiangolo/fastapi/issues/754
# https://github.com/auredentan/starlette-session/blob/master/examples/memcache_example.py
from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.security import APIKeyCookie
from fastapi.responses import HTMLResponse
from starlette.responses import Response, HTMLResponse
from starlette import status
from jose import jwt


#'''
async def authenticate(request, payload, SESSION_SECRET, response=Response):
    cookie_sec = APIKeyCookie(name="session")
    users = {"dmontagu": {"password": "secret1"}, "tiangolo": {"password": "secret2"}}

    async def get_current_user(session: str = Depends(cookie_sec)):
        try:
            payload = jwt.decode(session, SESSION_SECRET)
            return users[payload["sub"]]
        except Exception: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid authentication")

    async def read_private(username: str = Depends(get_current_user)):
        return {"username": username, "private": "get some private data"}

    if 'login' == payload['page_requested']:#in payload['query_params']:
        if request.method == "GET":
            return HTMLResponse(content="""<html>
                <form action="/login" method="post">
                Username: <input type="text" name="username" required>
                <br>
                Password: <input type="password" name="password" required></br>
                <input type="submit" value="Login">
                </form></html>""", status_code=200, media_type='text/html')
        forms_needed = ["username", "password"]
        if request.method == "POST" and all(f in payload["form_data"].keys() for f in forms_needed):
            f = payload["form_data"]
            username, password = f["username"], f["password"]
            if username not in users: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user or password")
            db_password = users[username]["password"]
            if not password == db_password: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user or password")
            token = jwt.encode({"sub": username}, SESSION_SECRET)
            print(token)
            response.set_cookie("session", token)
            return {"ok": True}
    if 'private' in payload['query_params'] and request.method == "GET": read_private()

    if 'logout' in payload['query_params'] and request.method == "GET":
        response.delete_cookie("session")
        return {"ok": True}
#'''