import sys
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from os.path import dirname, basename, isfile, join, realpath
from os import chdir, getcwd, name as os_name, listdir

if __package__ is None or __package__ == '':
    # uses current directory visibility
    from db import frontEnd2DB, Database, checkIfUsersTableExist, createUsersDB
else:
    # uses current package visibility
    sys.path.append(".")
    from .db import frontEnd2DB, Database, checkIfUsersTableExist, createUsersDB
import glob
import importlib

fs, parent, DB, module_2_import = "\\" if os_name == 'nt' else '/', dirname(realpath(__file__)), Database(), "routers"
templates_dir = parent+fs+"decoration"+fs+"templates"
templates = Jinja2Templates(directory=templates_dir)

app = FastAPI(debug=True)
app.mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static")

@app.on_event("startup")
async def DB_startup():
    await DB.connect()
    app.state.db = DB

@app.on_event("startup")
async def load_all(module_2_import=module_2_import):
    if getcwd().find(fs+"app") == -1: chdir("app"+fs)
    if getcwd().find(module_2_import) == -1: chdir(module_2_import)
    modules = glob.glob(join(getcwd(), "*.py"))
    __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    if getcwd().find(module_2_import) >= 0: chdir('..')
    try: all_modules = [importlib.import_module(module_2_import+'.'+i) for i in __all__]
    except Exception as e: raise e
    names = {(m.__name__, x):m for m in all_modules for x in m.__dict__ if not x.startswith("_")}
    globals_dict = {module_meta[0][len(module_2_import)+1:]+'_'+module_meta[1]: getattr(module_data, module_meta[1]) for module_meta, module_data in names.items()}
    globals_dict['options'] = {str(x):y for x, y in globals_dict.items()}
    globals_dict['html_templates'] = [f for f in listdir(templates_dir) if f.endswith(".html")]
    globals().update(globals_dict)

@app.on_event("startup")
async def create_users_db():
    if await checkIfUsersTableExist(db_conn=app.state.db) == True: pass
    else: await createUsersDB(db_conn=app.state.db)


@app.api_route("/", methods=["GET", "POST"])
@app.api_route("/{Path_Param1}/{rest_of_path:path}", methods=["GET", "POST"])
async def root(request: Request, Path_Param1: str='index', rest_of_path: str=''):
    # request.url.path ~~== request["path_params"]
    path_exceptions, err_page = ["forbidden"], "forbidden/403"
    payload = {"path":request.url.path}
    path_params = request["path_params"]
    if len(path_params) > 0: Path_Param1 = path_params['Path_Param1']
    if Path_Param1 not in path_exceptions: 
        if Path_Param1 == '': Path_Param1 = 'index'
        payload["page_requested"] = Path_Param1
        payload["form_data"] = {x[0]:x[1] for x in list((await request.form()).items())}
        payload["path_params"] = [x for x in path_params["rest_of_path"].split('/') if x is not None and x!=''] if "rest_of_path" in path_params else None
        qp2d = str(request["query_string"].decode("utf-8")) # 'qp2d' aka "Query Parameters *to* Dict"
        payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2d.split("&")} if qp2d.find('=') > -1 and len(qp2d) >= 3 else {}
        Path_Param1 = Path_Param1 + ".html" if Path_Param1.find(".html") == -1 else Path_Param1
        renderer = Path_Param1[0:Path_Param1.find(".html")] + "_main" # i.e.: 1stPathParam="ex" -> there is "ex.py"@routers dir (that's a module) -> Call it's "main" function.
        payload.update(await frontEnd2DB(payload, request))
        if renderer in options:
            select_func = (renderer, {"request":request, "payload":payload, "templates":templates})
            return await options[select_func[0].replace("'", "")](*select_func[1].values())
        elif Path_Param1 in html_templates: return templates.TemplateResponse(Path_Param1, {"request": request, "payload": payload})
        else: err_page = "404"
    return templates.TemplateResponse(err_page+".html", {"request": request})
