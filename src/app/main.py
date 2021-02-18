from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse
from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette_session import SessionMiddleware

from collections import defaultdict
from os.path import dirname, basename, isfile, join, realpath
from os import chdir, getcwd, environ, name as os_name, listdir
from asyncinit import asyncinit
from jose import jwt
import sys, json, glob, importlib

if __package__ is None or __package__ == '':
    # uses current directory visibility
    from system.db import db_query, front_End_2DB, Database, generate_basic_DB_tables, populate_privileges_DB_table
    from system.auth import *
    from system.utilities import convert_your_html_files
else:
    # uses current package visibility
    sys.path.append(".")
    from .system.db import db_query, front_End_2DB, Database, generate_basic_DB_tables, populate_privileges_DB_table
    from .system.auth import *
    from .system.utilities import convert_your_html_files

fs, parent, DB, module_2_import = "\\" if os_name == 'nt' else '/', dirname(realpath(__file__)), Database(), "routers"
templates_dir = parent+fs+"decoration"+fs+"templates"
templates = Jinja2Templates(directory=templates_dir)
SESSION_SECRET = environ["SESSION_SECRET"]
do_you_want_users = True if "DO_YOU_WANT_USERS" in environ and environ["DO_YOU_WANT_USERS"] == "True" else False
where_am_i = environ["WHERE_AM_I"] if "WHERE_AM_I" in environ and environ["WHERE_AM_I"] not in ('', None) else "PRODUCTION"

async def Auth(request, payload, URL=None):
    Session_Decoded = jwt.decode(request.session["session"], SESSION_SECRET) if "session" in request.session else {}
    user, mandatory_login, mandatory_logout = Session_Decoded['username'] if 'username' in Session_Decoded else None, False, False
    if do_you_want_users==True and user is not None and user in users.keys() and URL in privileges and len(privileges[URL]) > 0: user_has_access = any(g in users[user]['roles'] for g in privileges[URL])
    elif URL in privileges and len(privileges[URL]) > 0 and user is None: mandatory_login, user_has_access = True, False
    elif URL not in privileges or len(privileges[URL]) == 0: user_has_access = True
    else: user_has_access = False
    server_sessions_tokens = {data['token']:username for username, data in server_sessions.items()}
    if not ("session" in request.session and request.session["session"] in server_sessions_tokens) and user is not None: mandatory_logout = True
    if URL == 'register':
        if user in users and 'roles' in users[user] and 'registrant' in users[user]['roles']: return await register(request=request, payload=payload, Session_Decoded=Session_Decoded, SESSION_SECRET=SESSION_SECRET, render_template=templates.TemplateResponse, Server_Sessions=server_sessions, users=users)
        elif user is not None: user_has_access = False
        else: mandatory_login = True
    if URL == 'login' or mandatory_login: return await login(request=request, payload=payload, users=users, SESSION_SECRET=SESSION_SECRET, Server_Sessions=server_sessions, render_template=templates.TemplateResponse)
    if URL == 'logout' or mandatory_logout: return await logout(request=request, Session_Decoded=Session_Decoded, Server_Sessions=server_sessions, render_template=templates.TemplateResponse)
    return user_has_access

async def root(request: Request):
    path_exceptions, err_page = ["forbidden"], "forbidden/403"
    payload = {"path":request.url.path}
    path_params = request["path_params"]
    URL = path_params["URL"] if "URL" in path_params else 'index'
    full_path = URL if 'rest_of_path' not in path_params else URL + "/" + path_params["rest_of_path"]
    await load_users_privileges_sessions_DBQueries(reload_g="users") #sessions
    payload["page_requested"] = URL
    payload["form_data"] = {x[0]:x[1] for x in list((await request.form()).items())}
    payload["path_params"] = [x for x in path_params["rest_of_path"].split('/') if x is not None and x!=''] if "rest_of_path" in path_params else None
    qp2d = str(request["query_string"].decode("utf-8")) # 'qp2d' aka "Query Parameters *to* Dict"
    payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2d.split("&")} if qp2d.find('=') > -1 and len(qp2d) >= 3 else {}
    user_has_access = await Auth(request=request, payload=payload, URL=URL) if URL not in path_exceptions else False
    if type(user_has_access) in (HTMLResponse, RedirectResponse) or str(type(user_has_access)) == "<class 'starlette.templating._TemplateResponse'>": return user_has_access
    if user_has_access == True:
        payload.update(await front_End_2DB(payload, request))
        URL = URL + ".html" if URL.find(".html") == -1 else URL
        renderer = URL[0:URL.find(".html")] + "_main"
        if renderer in options: 
            select_func = (renderer, {"request":request, "payload":payload, "render_template":templates.TemplateResponse})
            return await options[select_func[0].replace("'", "")](select_func[1].values)
        elif URL in html_templates: return templates.TemplateResponse(URL, {"request": request, "payload": payload})
        else: err_page = "404"
    return templates.TemplateResponse(err_page+".html", {"request": request})

async def DB_startup():
    await DB.connect()
    app.state.db = DB

async def utility_initializers():
    await convert_your_html_files(where_am_i)        

async def load_all(module_2_import=module_2_import):
    if getcwd().find(fs+"app") == -1: chdir("app"+fs)
    if getcwd().find(module_2_import) == -1: chdir(module_2_import)
    modules = glob.glob(join(getcwd(), "*.py"))
    __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    if getcwd().find(module_2_import) >= 0: chdir('..')
    try: all_modules = [importlib.import_module(module_2_import+'.'+i) for i in __all__]
    except Exception as e: raise e
    names = {(m.__name__, x):m for m in all_modules for x in m.__dict__ if x=='main'}
    globals_dict = {module_meta[0][len(module_2_import)+1:]+'_'+module_meta[1]: getattr(module_data, module_meta[1]) for module_meta, module_data in names.items()}
    globals_dict['options'] = {str(x):y for x, y in globals_dict.items()}
    globals_dict['html_templates'] = [f for f in listdir(templates_dir) if f.endswith(".html")]
    globals().update(globals_dict)

# I love that kind of mindset!!! Thank you!!!: https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
@asyncinit
class Singleton(type):
    _instances = {}
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances: cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

@asyncinit
class Privileges:
    __metaclass__ = Singleton
    async def __init__(self):
        try:
            res = await db_query(r_obj=app.state.db, query_name="load_privileges", External=False)
            self.available = {r['endpoint']:{"ID":r["ID"], "meta":json.loads(r["meta"]), "roles":json.loads(r["roles"])} for r in res} 
        except: self.available = {}

@asyncinit
class Users:
    __metaclass__ = Singleton
    async def __init__(self):
        #try:
        res = await db_query(r_obj=app.state.db, query_name="load_users", External=False)
        self.available = {r['username']:{'ID':r['ID'], 'metadata':json.loads(r['metadata']), 'roles':json.loads(r['roles']), 'password':r['password']} for r in res} 
        #except: self.available = {}

@asyncinit
class Database:
    __metaclass__ = Singleton
    async def __init__(self):
        try:
            res = await db_query(r_obj=app.state.db, query_name="load_users", External=False)
            self.available = {r['username']:{'ID':r['ID'], 'metadata':json.loads(r['metadata']), 'roles':json.loads(r['roles'])} for r in res} 
        except: self.available = {}

@asyncinit
class Server_Sessions:
    __metaclass__ = Singleton
    async def __init__(self):
        self.available = defaultdict(dict)

async def discovered_endpoints():
    endpoints = {x.replace('_main', ''):"py" for x in options.keys()}
    endpoints.update({x.replace('.html', ''):"html" for x in html_templates if x.replace('.html', '') not in endpoints.keys()})
    return endpoints

async def basic_DB_tables(reload_all_DBQueries=False):
    if reload_all_DBQueries == False:
        privileges = await Privileges() if do_you_want_users == True else None
        endpoints = await discovered_endpoints()
        await generate_basic_DB_tables(db_conn=app.state.db, do_you_want_users=do_you_want_users, endpoints=endpoints, privileges=privileges, reload_all_DBQueries=reload_all_DBQueries)
    else: await generate_basic_DB_tables(db_conn=app.state.db, do_you_want_users=do_you_want_users, endpoints=None, privileges=None, reload_all_DBQueries=reload_all_DBQueries)

async def load_users_privileges_sessions_DBQueries(reload_g=False):
    das_globals = ['users', 'privileges', 'server_sessions', 'DBQueries']
    G = list(globals().keys())
    if (not all(g in G for g in das_globals)) or (reload_g is not False and reload_g in das_globals):
            if reload_g == 'users' or 'users' not in G: 
                globals().update({"users":dict({k:v for k,v in (await Users()).available.items()})})
            if reload_g == 'privileges' or 'privileges' not in G:
                globals().update({"privileges":dict({k:v['roles'] for k,v in (await Privileges()).available.items()})})
            if reload_g == 'server_sessions' or 'server_sessions' not in G:
                globals().update({"server_sessions":{username:metadata for username, metadata in (await Server_Sessions()).available.items()}})
            if reload_g == 'DBQueries': await basic_DB_tables(reload_all_DBQueries=True)
    elif (reload_g is not False and reload_g not in das_globals): raise Exception("Unknown Global Variable Requested to be Reloaded ->", reload_g)
    else: pass

routes = [
    Mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static"),
    Route("/", endpoint=root, methods=["GET", "POST"]),
    Route("/{URL}/{rest_of_path:path}", endpoint=root, methods=["GET", "POST"])
]

async def http_exception(request, exc):
    try:
        if exc.status_code == 500: message = "Lovely Day!"
        elif exc.status_code == 403: message = str(exc.detail)
        else: message = "Lovely Day!"
    except AttributeError: message = str(exc)
    return HTMLResponse(content="""<html> <head>
                <style>
                    * {
                        margin: 0;
                        padding: 0;
                    }
                    .imgbox {
                        display: grid;
                        height: 100%;
                    }
                    .center-fit {
                        max-width: 100%;
                        max-height: 100vh;
                        margin: auto;
                    }
                </style>
            </head>
            <body>
            <h1>This is what happened: {message} </h1>
            <h4>~ “All work and no play makes devs dull boys.”</h4>
            <div class="imgbox">
                <img class="center-fit" src='https://i.redd.it/s550dkwyk8621.jpg'>
            </div>
            </body>
            </html>""".replace("message", message), status_code=200, media_type='text/html')

exception_handlers = {
    #404: not_found,
    403: http_exception,
    500: http_exception
}

app = Starlette(debug=True if where_am_i in ("development", "docker_dev") else False , routes=routes, on_startup=[DB_startup, utility_initializers, load_all, basic_DB_tables, load_users_privileges_sessions_DBQueries], exception_handlers=exception_handlers)
app.add_middleware(SessionMiddleware, secret_key="secret", cookie_name="session")
#app.mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static")