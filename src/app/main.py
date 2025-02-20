from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import (
    HTMLResponse,
    RedirectResponse,
)  # , Response
from starlette.staticfiles import StaticFiles
from starlette.templating import _TemplateResponse

from starlette.middleware.sessions import SessionMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette_csrf.middleware import CSRFMiddleware

from typing import Union
from collections import defaultdict as dd
from asyncinit import asyncinit
from json import loads

from app.system.db import (
    _db_query,
    Query_DB,
    DB
)
from app.system.constants import (
    WHERE_AM_I,
    SESSION_MAX_AGE,
    CORS_MAX_AGE,
    COOKIE_SECRET,
    CSRF_SECRET,
    PATH_EXCEPTIONS,
    EXCEPTIONS,
    ERROR_PAGE,
    RESERVED_KEYWORDS,
    static_dir,
    ENDPOINT_KEYS_FROM_DB
)
from app.system.tools import (
    re_eval, utility_initializers,
    templates, save_up_files, 
    load_all, basic_DB_tables
)
from app.system.html_input2json import make_dict_from_dotted_string
from app.system.auth import Auth
from app.system.http_exception_handling import EXCEPTION_HANDLERS

FIRST_RUN = True

ACCEPTABLE_DIRECT_RESPONSES = (HTMLResponse, RedirectResponse, _TemplateResponse,)

(
    USERS, ENDPOINTS, SERVER_SESSIONS, 
    PY_RENDERS, HTML_TEMPLATES, DB_QUERIES
) = [{}] * 6


async def DB_startup():
    global DB_QUERIES
    await DB.connect()
    app.state.db = DB


async def ForceLogout(request: Request, payload):
    return await Auth(
        request=request, payload=payload,
        USERS=USERS, ENDPOINTS=ENDPOINTS,
        SERVER_SESSIONS=SERVER_SESSIONS, URL="logout"
    )


async def root(request: Request):
    payload = {
        "path": request.url.path, 
        "form_data": dd(list),
        "path_params": None,
        "query_params": {},
    }
    path_params = request["path_params"]
    URL = path_params.get("URL", "index")
    if path_params.get("rest_of_path", None) is not None:
        URL += "/" + path_params.get("rest_of_path", "")
    if URL.endswith("/"):
        URL = URL[:-1]
    payload["full_path"] = URL
    URL_clean_name = URL.replace(".html", "")
    URL_template_name = f'{URL_clean_name}.html'

    is_url_exception = any([
        url in EXCEPTIONS
        for url in [URL, URL_clean_name]
    ])
    if not is_url_exception:
        # Temporarily deactivated
        if False:
            await load_basic_globals(reload_variable="DB_QUERIES")
        payload["page_requested"], payload["request.method"] = URL, request.method

        form = await request.form()
        for x in form.multi_items():
            payload["form_data"][x[0]].append(x[1])

        payload["form_data"] = {
            k: v[0] if len(v) == 1 and k not in RESERVED_KEYWORDS["form_data"] else v
            for k, v in payload["form_data"].items()
        }

        if "rest_of_path" in path_params:
            payload["path_params"] = [
                x 
                for x in path_params["rest_of_path"].split("/") 
                if x not in [None, ""]
            ]
        
        # '_qp2d' aka "Query Parameters *to* Dict"
        _qp2d = str(request["query_string"].decode("utf-8"))
        if len(_qp2d) >= 1 and _qp2d[-1] == "&":
            _qp2d = _qp2d[:-1]
        # `>= 3`, means that there's at least one k=v query parameter:
        pattern_of_min_query_parameter = 'k=v'
        if "=" in _qp2d and len(_qp2d) >= len(pattern_of_min_query_parameter):
            payload["query_params"] = {
                arg.split("=")[0]: arg.split("=")[1] 
                for arg in _qp2d.split("&")
            }

        user_has_access = False
        if not any([URL.startswith(x) for x in PATH_EXCEPTIONS]):
            user_has_access = await Auth(
                request=request, payload=payload, 
                USERS=USERS, ENDPOINTS=ENDPOINTS, 
                SERVER_SESSIONS=SERVER_SESSIONS, URL=URL
            )
        
        if isinstance(user_has_access, ACCEPTABLE_DIRECT_RESPONSES):
            return user_has_access

        if user_has_access is True:
            payload["form_data"] = await make_dict_from_dotted_string(
                await save_up_files(payload["form_data"]),
                input_name_str_exception="Uploads",
            )
            init_query = (ENDPOINTS
                .get(URL_clean_name, {})
                .get("init_query", None)
            )
            payload.update(await Query_DB(payload, request, init_query=init_query))

            validators = (ENDPOINTS
                .get(URL_clean_name, {})
                .get("validators", None)
            )
            evaluated_validators = await re_eval(
                validators=validators, payload_=payload
            )
            if validators is not None and not evaluated_validators:
                raise Exception("Endpoing Validation Failed!")

            server_sessions_tokens = await SERVER_SESSIONS.server_sessions_tokens()
            if "session" in request.session:
                active_user = server_sessions_tokens.get(request.session["session"])
                #if active_user is None:

                server_side_session_payload = (
                    ENDPOINTS
                    .get(URL.replace(".html", ""), {})
                    .get(request.method, {})
                    .get("server_side_session_payload", None)
                )
                if server_side_session_payload is not None:
                    extra_server_side_session_data = await re_eval(
                        server_side_session_payload, payload, True
                    )

                    try:
                        SERVER_SESSIONS.available[active_user]["data"].update(
                            extra_server_side_session_data
                        )
                    except KeyError:
                        return await ForceLogout(request, payload)

                payload.update(
                    {
                        "session": {
                            "username": active_user,
                            "server": SERVER_SESSIONS.available[active_user].get("data"),
                            "client": request.session.get("session"),
                        }
                    }
                )
            else:
                payload.update({"session": {}})
            
            # We want to cover cases where the user typed `py|html_endpoint.html`
            renderer = f"{URL_clean_name}_main"
            if renderer in PY_RENDERS:
                func_payload = {
                    "request": request,
                    "payload": payload,
                    "render_template": templates.TemplateResponse,
                    "Query_DB": Query_DB,
                    "Session": SERVER_SESSIONS,
                }
                select_func = (renderer, func_payload)
                return await PY_RENDERS[select_func[0].replace("'", "")](
                    select_func[1].values
                )
            elif URL_clean_name in ENDPOINTS.keys():
                return templates.TemplateResponse(
                    URL_template_name, {"request": request, "payload": payload}
                )
            elif URL_template_name == "file_download.html":
                return await save_up_files(
                    init_form=payload["query_params"], download=True
                )
    
    if payload.get("session") in [None, {}]:
        return await ForceLogout(request, payload)
    return templates.TemplateResponse(ERROR_PAGE + ".html", {"request": request})

# I love that kind of mindset!!! Thank you!!!: https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
@asyncinit
class Singleton(type):
    _instances = {}

    async def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

@asyncinit
class Endpoints:
    __metaclass__ = Singleton

    async def __init__(self):
        try:
            res = await _db_query(
                r_obj=DB, 
                query_name="load_endpoints", 
                External=False
            )
            self.available = {
                r["endpoint"]: {
                    "ID": r["ID"],
                    "meta": loads(r["meta"]),
                    "roles": loads(r["roles"]),
                }
                for r in res
            }
        except:
            self.available = {}

@asyncinit
class Users:
    __metaclass__ = Singleton

    async def __init__(self):
        res = await _db_query(
            r_obj=DB, 
            query_name="load_users", 
            External=False
        )
        self.available = {
            r["username"]: {
                "ID": r["ID"],
                "metadata": loads(r["metadata"]),
                "roles": loads(r["roles"]),
                "password": r["password"],
            }
            for r in res
        }

@asyncinit
class Server_Sessions:
    __metaclass__ = Singleton

    async def __init__(self):
        self.available = dd(dict)

    async def _ad_hoc_(self, session_str, username_str):
        if self.available.get(username_str, {}).get('token') == session_str:
            return False
        
        self.available[username_str] = {'token': session_str}
        return True

    async def server_sessions_tokens(self):
        return {
            data["token"]: username 
            for username, data in self.available.items()
        }


async def load_basic_globals(
    reload_variable: Union[str, bool] = False
):
    global USERS
    global ENDPOINTS
    global SERVER_SESSIONS
    global DB_QUERIES
    global PY_RENDERS
    global HTML_TEMPLATES
    global FIRST_RUN
    global DB

    mapping = {
        'USERS': USERS,
        'ENDPOINTS': ENDPOINTS,
        'SERVER_SESSIONS': SERVER_SESSIONS,
        'DB_QUERIES': DB_QUERIES
    }
    
    uninitialized_global_variables = [name for name, var in mapping.items() if var == {}]
    if isinstance(reload_variable, str):
        uninitialized_global_variables.append(reload_variable)
    
    if (
        isinstance(reload_variable, str) and 
        reload_variable not in mapping
    ):
        raise Exception(f'''
            Unknown Global Variable Requested to be Reloaded:
            {reload_variable}
        ''')
    
    if 'DBQueries' in uninitialized_global_variables:
        await basic_DB_tables(
            _py_renders=PY_RENDERS,
            _html_templates=HTML_TEMPLATES,
            db_conn=DB,
            _endpoints=ENDPOINTS,
            reload_all_DBQueries=True
        )

    if "USERS" in uninitialized_global_variables:
        USERS = dict((await Users()).available.items())
    if "ENDPOINTS" in uninitialized_global_variables:
        available_endpoints = (await Endpoints()).available
        ENDPOINTS = {
            k: {
                x: v.get(x, v["meta"].get(x, {}))
                for x in ENDPOINT_KEYS_FROM_DB
            }
            for k, v in available_endpoints.items()
        }
    if "SERVER_SESSIONS" in uninitialized_global_variables:
        SERVER_SESSIONS = await Server_Sessions()
    
    if FIRST_RUN:
        PY_RENDERS, HTML_TEMPLATES = await load_all()
        await basic_DB_tables(
            _py_renders=PY_RENDERS,
            _html_templates=HTML_TEMPLATES,
            db_conn=DB,
            _endpoints=await Endpoints(),
            reload_all_DBQueries=True
        )
        FIRST_RUN = False

routes = [
    Mount("/static/", StaticFiles(directory=static_dir), name="static"),
    Route("/", endpoint=root, methods=["GET", "POST"]),
    Route("/{URL}/{rest_of_path:path}", endpoint=root, methods=["GET", "POST"]),
]


app = Starlette(
    debug=True if WHERE_AM_I in ("development", "docker_dev",) else False,
    routes=routes,
    exception_handlers=EXCEPTION_HANDLERS,
    on_startup=[
        DB_startup,
        utility_initializers,
        load_basic_globals,
    ],
)
app.add_middleware(
    SessionMiddleware,
    secret_key=COOKIE_SECRET,
    session_cookie="session",
    max_age=SESSION_MAX_AGE,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["hr.nepheli.org", "localhost"],
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
    allow_credentials=True,
    expose_headers=["*"],
    max_age=CORS_MAX_AGE,
)
app.add_middleware(
    CSRFMiddleware,
    secret=CSRF_SECRET,
    cookie_secure=True,
    sensitive_cookies="session",
    cookie_name="csrf_cookie",
)

if __name__ == "__main__":
    pass
