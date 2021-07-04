from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from starlette.routing import Route
from starlette.exceptions import HTTPException
from starlette import status
from starlette_session import SessionMiddleware
from jose import jwt
from datetime import datetime as dt
from bcrypt import hashpw, gensalt
from json import loads
from sys import path as sys_path

if __package__ is None or __package__ == '':
    # uses current directory visibility
    from db import db_query
else:
    # uses current package visibility
    sys_path.append(".")
    from .db import db_query

async def login(request: Request, payload, SESSION_SECRET, render_template, Server_Sessions=None, users=None):
    #return HTMLResponse(content=""" """.format(previous_page=payload["page_requested"]), status_code=200, media_type='text/html')
    valid_login = False
    if request.method == "GET" or payload is None: 
        existing_query_params = '?'+'&'.join([k+'='+v for k,v in payload['query_params'].items()]) if len(payload['query_params']) > 0 else ''
        payload['page_requested'] += existing_query_params
        return render_template('forbidden/system/auth/login.html', {"request": request, "payload": payload})
    forms_needed = ["username", "password"]
    if request.method == "POST" and type(payload) == dict and all(f in payload["form_data"].keys() for f in forms_needed):
        f = payload["form_data"]
        username, password = f["username"], f["password"]
        if username in users:
            db_password = users[username]["password"]
            try: check_hash = hashpw(password, db_password)
            except(TypeError, ValueError):
                password, db_password = password.encode('utf-8'), db_password.encode('utf-8')
                check_hash = hashpw(password, db_password)
            valid_login = check_hash == db_password
        if not valid_login: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user or password #0")
        token = jwt.encode({"username": username, "data": str(dt.now())}, SESSION_SECRET, algorithm="HS256")
        request.session.update({"session": token})
        Server_Sessions[username] = {"token":token, "data":{"Don't":"tell", "i.e.":str(dt.now())}}
        page_redirect = payload["form_data"]["previous_page"] if payload["form_data"]["previous_page"].find("login") == -1 else "index"
        return RedirectResponse(url="/"+page_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT)

async def logout(request: Request, Session_Decoded, Server_Sessions, render_template, payload):
    Server_Sessions.pop(Session_Decoded['username'] if 'username' in Session_Decoded else None, None)
    request.session.clear()
    return render_template('forbidden/system/auth/logout.html', {"request": request, "payload":payload})

async def register(request, payload, Session_Decoded, SESSION_SECRET, Server_Sessions, users, render_template):
    if request.method == "GET" or payload is None: return render_template('forbidden/system/auth/register.html', {"request": request, "payload": payload})
    forms_needed = ["username", "password", "password2", "roles", "metadata"]
    if request.method == "POST" and type(payload) == dict and all(f in payload["form_data"].keys() for f in forms_needed):
        f = payload["form_data"]
        username, password, password2 = f["username"].replace("'", ""), f["password"].replace("'", ""), f["password2"].replace("'", "")
        if username in users.keys(): raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="This username is already taken!")
        if not password == password2: raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid user or password #2")
        try: hashpass = hashpw(password, gensalt(13)).encode('utf-8')
        except TypeError: hashpass = hashpw(password.encode("utf-8"), gensalt(13))
        faulty_forms = ""
        try: roles = loads(f["roles"])
        except: faulty_forms = "Roles"
        try: metadata = loads(f["metadata"])
        except: faulty_forms = "Metadata" if faulty_forms == "" else faulty_forms+" & Metadata"
        if faulty_forms != "": raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=faulty_forms+" Must be Valid JSON!")
        await db_query(r_obj=request.app.state.db, query_name="create_new_user", External=False, query_payload={"username":username, "hashpass":hashpass.decode("utf-8") , "roles":roles, "metadata":metadata})
        token = jwt.encode({"username": username, "data": str(dt.now())}, SESSION_SECRET)
        request.session.update({"session": token})
        Server_Sessions[username] = {"token":token, "data":{"Don't":"tell", "i.e.":str(dt.now())}}
        page_redirect = "index"
        return HTMLResponse(content="""<html>All Good, User ("{new_user}") Has Been Registered</html>""".format(new_user=username), status_code=200, media_type='text/html')