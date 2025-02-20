from functools import reduce as rdc
from operator import mul
from starlette.requests import Request
from starlette.responses import HTMLResponse, RedirectResponse  # Response
from starlette import status
from starlette.exceptions import HTTPException
from jose import jwt
from datetime import datetime as dt
from bcrypt import hashpw, gensalt
from json import loads

from app.system.constants import WHERE_AM_I
from app.system.db import _db_query
from app.system.tools import (
    re_eval, templates
)
from app.system.constants import (
    SESSION_SECRET,
    JWT_OPTIONS,
    DO_YOU_WANT_USERS,
)


async def Auth(
    request, payload,
    USERS, ENDPOINTS, SERVER_SESSIONS, 
    URL=None,
):
    mandatory_login, mandatory_logout = False, False
    Session_Decoded = (
        jwt.decode(
            request.session["session"],
            SESSION_SECRET,
            options=JWT_OPTIONS,
            algorithms="HS256",
        )
        if "session" in request.session
        else {}
    )
    user = Session_Decoded["username"] if "username" in Session_Decoded else None

    if (
        DO_YOU_WANT_USERS is True
        and user in USERS.keys()
        and len(ENDPOINTS.get(URL, {}).get("roles", {})) > 0
    ):
        roles = ENDPOINTS[URL]["roles"]
        if isinstance(roles, list):
            endpoint_roles = ENDPOINTS[URL]["roles"]
        elif isinstance(roles, dict):
            endpoint_roles = ENDPOINTS[URL]["roles"].get(
                request.method, "UNKNOWN!")
        else:
            raise Exception(f"UNKNOWN DB TYPE FOR {ENDPOINTS[URL]['roles']}!")

        # TODO: something better than a func
        def has_user_any_role(roles): return any(
            g in USERS[user]["roles"] for g in roles)

        if isinstance(endpoint_roles, list):
            user_has_access = has_user_any_role(endpoint_roles)
        elif isinstance(endpoint_roles, dict):
            payload, user_has_access = payload, True
            conditions = (c for c in endpoint_roles.keys() if c != "default")
            # TODO: all will do:
            user_has_access = rdc(
                mul,
                [
                    has_user_any_role(endpoint_roles[c])
                    if await re_eval(c, payload)
                    else has_user_any_role(endpoint_roles["default"])
                    for c in conditions
                ],
            )
        else:
            raise Exception("Endpoint Roles Don't Have a Valid Data Type!")
    elif (
        URL in ENDPOINTS and
        len(ENDPOINTS[URL]["roles"]) > 0 and
        user is None
    ):
        mandatory_login, user_has_access = True, False
    elif (
        URL not in ENDPOINTS or
        len(ENDPOINTS[URL]["roles"]) == 0
    ):
        user_has_access = True
    else:
        user_has_access = False

    server_sessions_tokens = await SERVER_SESSIONS.server_sessions_tokens()
    if (
        not server_sessions_tokens.get(request.session.get("session"), False)
        and user is not None
    ):
        # `if BOOL` is used as a switch during local development:
        if True and WHERE_AM_I in ("development", "docker_dev",):
            await SERVER_SESSIONS._ad_hoc_(request.session.get("session"), user)
        else:
            mandatory_logout = True

    if URL == "register":
        if USERS.get(user, {}).get("roles").get("registrant", None) is not None:
            return await register(
                request=request,
                payload=payload,
                users=USERS,
                Session_Decoded=Session_Decoded,
                SESSION_SECRET=SESSION_SECRET,
                Server_Sessions=SERVER_SESSIONS,
                render_template=templates.TemplateResponse,
            )
        elif user is not None:
            user_has_access = False
        else:
            mandatory_login = True
    if URL == "login" or mandatory_login:
        return await login(
            request=request,
            payload=payload,
            users=USERS,
            SESSION_SECRET=SESSION_SECRET,
            Server_Sessions=SERVER_SESSIONS,
            render_template=templates.TemplateResponse,
        )
    if URL == "logout" or mandatory_logout:
        return await logout(
            request=request,
            payload=payload,
            Session_Decoded=Session_Decoded,
            Server_Sessions=SERVER_SESSIONS,
            render_template=templates.TemplateResponse,
        )
    return user_has_access


async def login(
    request: Request,
    payload,
    SESSION_SECRET,
    render_template,
    Server_Sessions=None,
    users={},
):
    valid_login = False
    if request.method == "GET" or payload is None:
        existing_query_params = (
            "&".join([f"{k}={v}" for k, v in payload["query_params"].items()])
            if len(payload["query_params"]) > 0
            else ""
        )
        existing_query_params = f"?{existing_query_params}"
        payload["page_requested"] += existing_query_params
        return render_template(
            "forbidden/system/auth/login.html", {"request": request, "payload": payload}
        )

    if (
        request.method == "POST"
        and isinstance(payload, dict)
        and all(f in payload["form_data"].keys() for f in ["username", "password"])
    ):
        f = payload["form_data"]
        username, password = f["username"], f["password"]
        if username in users.keys():
            db_password = users[username]["password"]
            try:
                check_hash = hashpw(password, db_password)
            except (TypeError, ValueError):
                password, db_password = password.encode("utf-8"), db_password.encode(
                    "utf-8"
                )
                check_hash = hashpw(password, db_password)
            valid_login = check_hash == db_password

        if not valid_login:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user or password #0",
            )

        token = jwt.encode(
            {"username": username, "data": str(dt.now())},
            SESSION_SECRET,
            algorithm="HS256",
        )
        request.session.update({"session": token})
        Server_Sessions.available[username] = {
            "token": token,
            "data": {"Don't": "tell", "Date": str(dt.now())},
            "ip": request.client,
        }
        page_redirect = (
            payload["form_data"]["previous_page"]
            if payload["form_data"]["previous_page"].find("login") == -1
            else "index"
        )
        return RedirectResponse(
            url="/" + page_redirect, status_code=status.HTTP_307_TEMPORARY_REDIRECT
        )


async def logout(
    request: Request, 
    Session_Decoded, 
    Server_Sessions, 
    render_template, 
    payload
):
    Server_Sessions.available.pop(Session_Decoded.get("username", None), None)
    request.session.clear()
    return render_template(
        "forbidden/system/auth/logout.html", {"request": request, "payload": payload}
    )


async def register(
    request,
    payload,
    Session_Decoded,
    SESSION_SECRET,
    Server_Sessions,
    users,
    render_template,
):
    if request.method == "GET" or payload is None:
        return render_template(
            "forbidden/system/auth/register.html",
            {"request": request, "payload": payload},
        )
    forms_needed = ["username", "password", "password2", "roles", "metadata"]
    forms_filled = all(f in payload["form_data"].keys() for f in forms_needed)
    if (
        request.method == "POST" and 
        isinstance(payload, dict) and 
        forms_filled
    ):
        f = payload["form_data"]
        username, password, password2, _, _ = [
            x.replace("'", "")
            for x in forms_needed
        ]

        if username in users.keys():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="This username is already taken!",
            )
        if not password == password2:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Invalid user or password #2",
            )
        
        try:
            hashpass = hashpw(password, gensalt(13)).encode("utf-8")
        except TypeError:
            hashpass = hashpw(password.encode("utf-8"), gensalt(13))

        other_user_data = {"roles": None, "metadata": None}
        for user_data in other_user_data.keys():
            try:
                other_user_data[user_data] = loads(f["roles"])
            except:
                pass

        faulty_forms = [k for k, v in other_user_data.items() if v is None]
        if len(faulty_forms) > 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forms {'&'.join(faulty_forms)} Must be in a Valid JSON format!",
            )

        await _db_query(
            r_obj=request.app.state.db,
            query_name="create_new_user",
            External=False,
            query_payload={
                "username": username,
                "hashpass": hashpass.decode("utf-8"),
                "roles": other_user_data["roles"],
                "metadata": other_user_data["metadata"],
            },
        )
        token = jwt.encode(
            {"username": username, "data": str(dt.now())}, SESSION_SECRET
        )
        request.session.update({"session": token})
        Server_Sessions[username] = {
            "token": token,
            "data": {"Don't": "tell", "i.e.": str(dt.now())},
        }

        # page_redirect = "index" ?
        return HTMLResponse(
            content=f"""<html>All Good, User ("{username}") Has Been Registered</html>""",
            status_code=200,
            media_type="text/html",
        )
