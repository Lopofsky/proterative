from starlette.applications import Starlette
from starlette.routing import Route, Mount
from starlette.requests import Request
from starlette.responses import Response, HTMLResponse, RedirectResponse, FileResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette_session import SessionMiddleware
from starlette_csrf import CSRFMiddleware

from base64 import b64decode   
from pathlib import Path
from collections import defaultdict as dd
from os.path import dirname, basename, isfile, join, realpath
from os import chdir, getcwd, environ, name as os_name, listdir, walk
from asyncinit import asyncinit
from jose import jwt
from inspect import getmembers, isfunction
from sys import path as sys_path
from json import loads
from glob import glob
from importlib import import_module
from shutil import copyfileobj
from urllib import parse as html_dec
from functools import reduce as rdc
from operator import mul  
from copy import deepcopy as dc

if __package__ is None or __package__ == '':
    # uses current directory visibility
    from system.db import db_query, Query_DB, Database, generate_basic_DB_tables, populate_endpoints_DB_table
    from system.html_input2json import make_dict_from_dotted_string
    from system.utilities import convert_your_html_files, text_san
    from system.auth import register, login, logout
    from system import jinja_filters
else:
    # uses current package visibility 
    sys_path.append(".")
    from .system.db import db_query, Query_DB, Database, generate_basic_DB_tables, populate_endpoints_DB_table
    from .system.html_input2json import make_dict_from_dotted_string
    from .system.utilities import convert_your_html_files, text_san
    from .system.auth import register, login, logout
    from .system import jinja_filters

path_exceptions, err_page, exceptions = ["forbidden"], "forbidden/403", ["favicon.ico"]
#"\\" if os_name == 'nt' else '/'
fs, parent, DB, module_2_import = {'nt':"\\"}.get(os_name, '/'), dirname(realpath(__file__)), Database(), "routers"
templates_dir = parent+fs+"decoration"+fs+"templates"
templates = Jinja2Templates(directory=templates_dir)
templates.env.add_extension('jinja2.ext.do')
templates.env.enable_async = True
custom_jinja_filters = {f[0]:f[1] for f in getmembers(jinja_filters, isfunction)}
templates.env.filters.update(custom_jinja_filters)
SESSION_SECRET, UPLOADS_PATH = environ["SESSION_SECRET"], environ["UPLOADS_PATH"].replace('"', '').replace("'", '')
do_you_want_users = bool(environ.get("DO_YOU_WANT_USERS", "False") == "True")
where_am_i = environ["WHERE_AM_I"] if environ.get("WHERE_AM_I", None) not in ('', None) else "PRODUCTION"

reserved_keywords = {'form_data':'query_names'}

async def root(request: Request):
    payload, path_params, err_page = {"path":request.url.path}, request["path_params"], '404'
    URL = path_params.get("URL", "index") if path_params.get('rest_of_path', None) is None else path_params.get("URL", "index")+'/'+path_params.get('rest_of_path', '')
    URL = URL if not URL.endswith('/') else URL[:-1]
    if URL not in exceptions:
        #await load_users_endpoints_sessions_DBQueries(reload_g="DBQueries") #sessions
        await load_users_endpoints_sessions_DBQueries(reload_g="endpoints")
        payload["page_requested"], payload["request.method"] = URL, request.method
        full_path = URL if 'rest_of_path' not in path_params else URL + "/" + path_params["rest_of_path"]
        payload["form_data"], form = dd(list), await request.form()
        for x in form.multi_items():
            payload["form_data"][x[0]].append(x[1])
        payload["form_data"] = {k:v[0] if len(v)==1 and k in reserved_keywords['form_data'] else v for k,v in payload["form_data"].items() }
        payload["path_params"] = [x for x in path_params["rest_of_path"].split('/') if x not in (None, '',)] if "rest_of_path" in path_params else None
        qp2d = str(request["query_string"].decode("utf-8")) # 'qp2d' aka "Query Parameters *to* Dict"
        if len(qp2d) >= 1 and qp2d[-1] == '&': qp2d = qp2d[:-1]
        payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2d.split("&")} if qp2d.find('=') > -1 and len(qp2d) >= 3 else {}
        user_has_access = await Auth(request=request, payload=payload, URL=URL) if not any([URL.startswith(x) for x in path_exceptions]) else False
        if type(user_has_access) in (HTMLResponse, RedirectResponse) or str(type(user_has_access)) == "<class 'starlette.templating._TemplateResponse'>": return user_has_access
        if user_has_access == True: 
            payload["form_data"] = await make_dict_from_dotted_string(await save_up_files(payload["form_data"]), input_name_str_exception="Uploads")
            init_query = endpoints.get(URL.replace('.html', ''), {}).get('init_query', None)
            payload.update(await Query_DB(payload, request, init_query=init_query))
            validators = endpoints.get(URL, {}).get('validators', None)
            if validators is not None and not await re_eval(validators=validators, payload_=payload): raise Exception("Endpoing Validation Failed!")
            server_sessions_tokens = await server_sessions.server_sessions_tokens()
            if "session" in request.session: 
                active_user = server_sessions_tokens[request.session["session"]]
                server_side_session_payload = endpoints.get(URL.replace('.html', ''), {}).get(request.method, {}).get('server_side_session_payload', None)
                if server_side_session_payload is not None:
                    extra_server_side_session_data = await re_eval(server_side_session_payload, payload, True)
                    server_sessions.available[active_user]["data"].update(extra_server_side_session_data)
                payload.update({"session":{"username":active_user, "server":server_sessions.available[active_user]["data"], "client":request.session.get('session')}})
            else: payload.update({"session":{}})
            URL = URL + ".html" if URL.find(".html") == -1 else URL
            renderer = URL[0:URL.find(".html")] + "_main"
            if renderer in options:
                select_func = (renderer, {"request":request, "payload":payload, "render_template":templates.TemplateResponse, "Query_DB":Query_DB})
                return await options[select_func[0].replace("'", "")](select_func[1].values)
            elif URL[0:URL.find(".html")] in endpoints.keys(): return templates.TemplateResponse(URL, {"request": request, "payload": payload})
            elif URL == 'file_download.html': return await save_up_files(init_form=payload["query_params"], download=True)
    return templates.TemplateResponse(err_page+".html", {"request": request})

async def utility_initializers():
    await convert_your_html_files(where_am_i)        

async def DB_startup():
    await DB.connect()
    app.state.db = DB

async def load_all(module_2_import=module_2_import):
    if getcwd().find(fs+"app") == -1: chdir("app"+fs)
    if getcwd().find(module_2_import) == -1: chdir(module_2_import)
    modules = glob(join(getcwd(), "*.py"))
    __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    if getcwd().find(module_2_import) >= 0: chdir('..')
    try: all_modules = [import_module(module_2_import+'.'+i) for i in __all__]
    except Exception as e: raise e
    names = {(m.__name__, x):m for m in all_modules for x in m.__dict__ if x=='main'}
    globals_dict = {module_meta[0][len(module_2_import)+1:]+'_'+module_meta[1]: getattr(module_data, module_meta[1]) for module_meta, module_data in names.items()}
    globals_dict['options'] = {str(x):y for x, y in globals_dict.items()}
    sub_path = 'templates'
    base_path = templates_dir.replace(sub_path, '')
    chdir(base_path)
    incompatible_html_paths = ('/', '\\')+tuple(path_exceptions)
    path_san = lambda x, suppl=False, s=sub_path: '/ ' if x.replace(s, '').replace('\\', '/')=='' and suppl else x.replace(s, '').replace('\\', '/')
    html_templates = {path_san(dirpath)+'/'+a_dir+'/' : [a_file 
                        for a_file in listdir(base_path+dirpath+'/'+a_dir+'/') 
                        if a_file.endswith(".html") and not a_dir.startswith(incompatible_html_paths)
                        ] 
                        for (dirpath, dirnames, filenames) in walk(sub_path) 
                        for a_dir in dirnames  
                        if not (
                            path_san(dirpath).startswith(incompatible_html_paths) 
                            if path_san(dirpath, True)[0] not in ['/', '/ ']
                            else path_san(dirpath)[1:].startswith(incompatible_html_paths)
                        )
                    }
    html_templates[''] = [f for f in listdir(sub_path) if f.endswith(".html")]
    html_templates = {k if not k.startswith(incompatible_html_paths) else k[1:] :v for k,v in html_templates.items()} 
    globals_dict['html_templates'] = html_templates
    globals().update(globals_dict)

async def Auth(request, payload, URL=None):
    jwt_options = {'verify_signature': True, 'verify_exp': True, 'verify_nbf': False, 'verify_iat': True, 'verify_aud': False}
    Session_Decoded = jwt.decode(request.session["session"], SESSION_SECRET, options=jwt_options, algorithms="HS256") if "session" in request.session else {}
    user, mandatory_login, mandatory_logout = Session_Decoded['username'] if 'username' in Session_Decoded else None, False, False
    if do_you_want_users==True and user in users.keys() and len(endpoints.get(URL, {}).get('roles', {})) > 0:
        if type(endpoints[URL]['roles']) == list: endpoint_roles = endpoints[URL]['roles']
        elif type(endpoints[URL]['roles']) == dict: endpoint_roles = endpoints[URL]['roles'].get(request.method, 'UNKNOWN!')
        else: raise Exception(f"UNKNOWN DB TYPE FOR {endpoints[URL]['roles']}!")
        has_user_any_role = lambda roles: any(g in users[user]['roles'] for g in roles)
        if type(endpoint_roles) is list: user_has_access = has_user_any_role(endpoint_roles)
        elif type(endpoint_roles) == dict: 
            payload, user_has_access = payload, True
            conditions = (c for c in endpoint_roles.keys() if c!="default")
            user_has_access = rdc(mul, [has_user_any_role(endpoint_roles[c]) if await re_eval(c, payload) else has_user_any_role(endpoint_roles["default"]) for c in conditions])
        else: raise Exception("Endpoint Roles Don't Have a Valid Data Type!")
    elif URL in endpoints and len(endpoints[URL]['roles']) > 0 and user is None: mandatory_login, user_has_access = True, False
    elif URL not in endpoints or len(endpoints[URL]['roles']) == 0: user_has_access = True
    else: user_has_access = False
    server_sessions_tokens = await server_sessions.server_sessions_tokens()
    if not server_sessions_tokens.get(request.session.get("session"), False) and user is not None:  mandatory_logout = True
    if URL == 'register':
        if users.get(user, {}).get('roles').get('registrant', None) is not None: return await register(request=request, payload=payload, Session_Decoded=Session_Decoded, SESSION_SECRET=SESSION_SECRET, render_template=templates.TemplateResponse, Server_Sessions=server_sessions, users=users)
        elif user is not None: user_has_access = False
        else: mandatory_login = True
    if URL == 'login' or mandatory_login: return await login(request=request, payload=payload, users=users, SESSION_SECRET=SESSION_SECRET, Server_Sessions=server_sessions, render_template=templates.TemplateResponse)
    if URL == 'logout' or mandatory_logout: return await logout(request=request, Session_Decoded=Session_Decoded, Server_Sessions=server_sessions, render_template=templates.TemplateResponse, payload=payload)
    return user_has_access

async def re_eval(validators, payload_, return_result=False):
    forbidden_s = ["from", "import", "exec", "eval", "__"]
    payload = dc(payload_)
    async def conditioning(validators, payload=payload):
        valid_conditions = False
        if type(validators) == str: validators = [validators]
        for x in validators:
            valid_conditions += int(eval(await text_san(x, forbidden_s), locals(), {'__builtins__':{}}))
        if valid_conditions != len(validators): return False
        return True
    if return_result:
        if type(validators) == dict:
            evaluated_result = {}
            for val, check in validators.items():
                cc = await conditioning(check, payload)
                if cc: 
                    try:
                        result = eval(await text_san(val, forbidden_s), locals(), {'__builtins__':{}})
                        if type(result) == dict: evaluated_result.update(result)
                        else: raise Exception("Evalution Failed #2!")
                    except: raise Exception("Evalution Failed #1!")
            return evaluated_result
    else: return await conditioning(validators)

# I love that kind of mindset!!! Thank you!!!: https://stackoverflow.com/questions/6760685/creating-a-singleton-in-python
@asyncinit
class Singleton(type):
    _instances = {}
    async def __call__(cls, *args, **kwargs):
        if cls not in cls._instances: cls._instances[cls] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]

@asyncinit
class Endpoints:
    __metaclass__ = Singleton
    async def __init__(self):
        try:
            res = await db_query(r_obj=app.state.db, query_name="load_endpoints", External=False)
            self.available = {r['endpoint']:{"ID":r["ID"], "meta":loads(r["meta"]), "roles":loads(r["roles"])} for r in res}
        except: self.available = {}

@asyncinit
class Users:
    __metaclass__ = Singleton
    async def __init__(self):
        res = await db_query(r_obj=app.state.db, query_name="load_users", External=False)
        self.available = {r['username']:{'ID':r['ID'], 'metadata':loads(r['metadata']), 'roles':loads(r['roles']), 'password':r['password']} for r in res} 

@asyncinit
class Server_Sessions:
    __metaclass__ = Singleton
    async def __init__(self): self.available = dd(dict)
    async def server_sessions_tokens(self): return {data['token']:username for username, data in self.available.items()}

async def discovered_endpoints():
    endpoints = {x.replace('_main', ''):"py" for x in options.keys()}
    incompatible_html_paths = ('/', '\\')+tuple(path_exceptions)
    endpoints.update({path+x.replace('.html', ''):"html" for path, end in html_templates.items() for x in end if x.replace('.html', '') not in endpoints.keys()})
    return endpoints

async def basic_DB_tables(reload_all_DBQueries=False):
    active_endpoints, endpoints = None, None
    if reload_all_DBQueries == False: 
        endpoints = await Endpoints() if do_you_want_users == True else None
        active_endpoints = await discovered_endpoints()
    await generate_basic_DB_tables(db_conn=app.state.db, do_you_want_users=do_you_want_users, active_endpoints=active_endpoints, endpoints=endpoints, reload_all_DBQueries=reload_all_DBQueries)

async def load_users_endpoints_sessions_DBQueries(reload_g=False):
    das_globals, G = ['users', 'endpoints', 'server_sessions', 'DBQueries'], list(globals().keys())
    if (not all(g in G for g in das_globals)) or (reload_g is not False and reload_g in das_globals):
            if reload_g == 'users' or 'users' not in G: 
                globals().update({"users":dict({k:v for k,v in (await Users()).available.items()})})
            if reload_g == 'endpoints' or 'endpoints' not in G:
                globals().update({"endpoints":dict(
                            {   
                                k:{
                                    x:v.get(x, v['meta'].get(x, {}))
                                    for x in ('init_query', 'validators', 'roles', 'GET', 'POST')
                                }
                                for k,v in (await Endpoints()).available.items()
                            }
                        )
                    }
                )
            if reload_g == 'server_sessions' or 'server_sessions' not in G: 
                globals().update({"server_sessions": await Server_Sessions()})
            if reload_g == 'DBQueries': 
                await basic_DB_tables(reload_all_DBQueries=True)
    elif (reload_g is not False and reload_g not in das_globals): 
        raise Exception("Unknown Global Variable Requested to be Reloaded ->", reload_g)
    else: pass

async def save_up_files(init_form, keyword='FILEUPLOAD', download=False):
    init_form = init_form
    global UPLOADS_PATH
    if download == False:
        form = {k:v for k,v in init_form.items()}
        for k, v in form.items():
            if k.find(keyword) > -1:
                custom_path = k[k.find(keyword)+len(keyword):].replace(".", "").replace("/", fs)
                path = UPLOADS_PATH+fs+custom_path+fs
                form_name = k[:k.find(keyword)]
                if form_name[-1] == '.': form_name = form_name[:-1]
                Path(path).mkdir(parents=True, exist_ok=True)
                v.file.seek(0)
                init_form.pop(k, None)
                if v.filename != '':
                    with open(path+v.filename, "wb") as buffer:
                        copyfileobj(v.file, buffer)
                    init_form[form_name] = {v.filename:{'path':path, 'content_type':v.content_type}}
                else: init_form[form_name] = None
        return init_form
    else:
        n = {}
        for k, v in init_form.items():
            t = html_dec.unquote(v) #unquote_plus
            if t.startswith(("'", '"')): t = t[1:]
            if t.endswith(("'", '"')): t = t[:-1]
            n[k] = t
        fileresponse = FileResponse(UPLOADS_PATH+fs+n['uuid']+fs+n['file'], media_type='application/octet-stream', filename=n['file'])
        return fileresponse

async def http_exception(request, exc):
    try:
        if exc.status_code == 500: message = "Lovely Day!"
        elif exc.status_code == 403: message = str(exc.detail)
        else: message = "Lovely Day!"
        if where_am_i not in ("development", "docker_dev") and exc.status_code == 500: message = "Please Contact the Administrator!"
    except AttributeError: message = str(exc)
    # Using python's "format", causes conflict with the CSS syntax.
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

exception_handlers = {403: http_exception, 500: http_exception}

routes = [Mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static"), Route("/", endpoint=root, methods=["GET", "POST"]), Route("/{URL}/{rest_of_path:path}", endpoint=root, methods=["GET", "POST"])]


app = Starlette(debug=True if where_am_i in ("development", "docker_dev") else False, routes=routes, exception_handlers=exception_handlers, on_startup=[DB_startup, utility_initializers, load_all, basic_DB_tables, load_users_endpoints_sessions_DBQueries])
app.add_middleware(SessionMiddleware, secret_key=environ.get('COOKIE_SECRET'), cookie_name="session", max_age=86400)
app.add_middleware(CSRFMiddleware, secret=environ.get('CSRF_SECRET'), cookie_secure=True, sensitive_cookies="session", cookie_name="csrf_cookie")
app.add_middleware(CORSMiddleware, allow_origins=['localhost'], allow_methods=['GET', 'POST'], allow_headers=['*'], allow_credentials=True, expose_headers=['*'], max_age=120)

if __name__ == '__main__': pass