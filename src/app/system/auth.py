from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from starlette.routing import Route
from starlette import status
from starlette_session import SessionMiddleware
from jose import jwt
import bcrypt

from datetime import datetime as dt

async def login(request: Request, payload, SESSION_SECRET, users=None):
    if request.method == "GET" or payload is None:
        return HTMLResponse(content="""<html>
            <form action="/login" method="post">
            Username: <input type="text" name="username" required>
            <br>
            Password: <input type="password" name="password" required></br>
            <input type="hidden" name="previous_page" value="{previous_page}">
            <input type="submit" value="Login">
            </form></html>""".format(previous_page=payload["page_requested"]), status_code=200, media_type='text/html')
    forms_needed = ["username", "password"]
    if request.method == "POST" and type(payload) == dict and all(f in payload["form_data"].keys() for f in forms_needed):
        f = payload["form_data"]
        username, password = f["username"], f["password"]
        db_password = users[username]["password"]
        if not password == db_password: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user or password")
        token = jwt.encode({"username": username, "data": str(dt.now())}, SESSION_SECRET)
        request.session.update({"session": token})
        return RedirectResponse(url="/"+payload["form_data"]["previous_page"], status_code=status.HTTP_307_TEMPORARY_REDIRECT)


async def logout(request: Request):
    request.session.clear()

async def register(Session_Decoded, request: Request):
    print(Session_Decoded)
    try: hashpass = bcrypt.hashpw(password,bcrypt.gensalt(13)).encode('utf-8')
    except TypeError: hashpass = bcrypt.hashpw(password.encode("utf-8"),bcrypt.gensalt(13))

'''
async def view_session(request: Request) -> JSONResponse:
    return JSONResponse({"session": request.session})
'''
