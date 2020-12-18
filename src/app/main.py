from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from routers import ping, index
from os.path import dirname, basename, isfile, join, realpath
from os import chdir, getcwd, name as os_name
from db import Database
import glob
import importlib
import sys
sys.path.append(".")

app = FastAPI(debug=True)

fs, parent, DB, module_2_import = "\\" if os_name == 'nt' else '/', dirname(realpath(__file__)), Database(), "routers"
templates = Jinja2Templates(directory=parent+fs+"decoration"+fs+"templates")
app.mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static")

@app.on_event("startup")
async def startup():
    await DB.connect()
    app.state.db = DB

def load_all(module_2_import):
    if getcwd().find(fs+"app") == -1: chdir("app"+fs)
    if getcwd().find(module_2_import) == -1: chdir(module_2_import)
    modules = glob.glob(join(getcwd(), "*.py"))
    __all__ = [basename(f)[:-3] for f in modules if isfile(f) and not f.endswith('__init__.py')]
    if getcwd().find(module_2_import) >= 0: chdir('..')
    try: all_modules = [importlib.import_module(module_2_import+'.'+i) for i in __all__]
    except Exception as e: raise e
    names = {(m.__name__, x):m for m in all_modules for x in m.__dict__ if not x.startswith("_")}
    globals_dict = {module_meta[0][len(module_2_import)+1:]+'_'+module_meta[1]: getattr(module_data, module_meta[1]) for module_meta, module_data in names.items()}
    globals().update(globals_dict)
    return {str(x):y for x, y in globals_dict.items()}

async def db_query(r_obj, query_name):
    queries = {"test":'''SELECT * FROM base WHERE "ID" IN (1,2) ''', "test2":'''SELECT * FROM base WHERE "ID"=3 '''} # todo: Redis
    return [{k:v for k,v in item.items()} for item in await r_obj.fetch_rows(queries[query_name])] if query_name in queries else [{"Requested Query":str(query_name), "Result": "Error! Query Name Not Found."}]

@app.route("/", methods=["GET", "POST"])
@app.route("/{Path_Param1}/{rest_of_path:path}", methods=["GET", "POST"])
async def root(request: Request, Path_Param1: str='index', rest_of_path: str=''):
    # request.url.path ~~== request["path_params"]
    path_exceptions = ['favicon.ico']
    payload = {"path":request.url.path}
    path_params = request["path_params"]
    if len(path_params) > 0: Path_Param1 = path_params['Path_Param1']
    #---------------- [START] DATABASE QUERIES FROM FORMS (?) ----------------
    # results = await db_query(r_obj=request.app.state.db, query_name="test")
    #---------------- [END] DATABASE QUERIES FROM FORMS (?) ------------------
    if Path_Param1 in path_exceptions: pass
    else:
        if Path_Param1 == '': Path_Param1 = 'index'
        options = load_all(module_2_import)
        payload["page_requested"] = Path_Param1
        payload["form_data"] = {x[0]:x[1] for x in list((await request.form()).items())}
        payload["path_params"] = [x for x in path_params["rest_of_path"].split('/') if x is not None and x!=''] if "rest_of_path" in path_params else None
        qp2d = str(request["query_string"].decode("utf-8")) # 'qp2d' aka "Query Parameters *to* Dict"
        payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2d.split("&")} if qp2d.find('=') > -1 and len(qp2d) >= 3 else None
        Path_Param1 = Path_Param1 + ".html" if Path_Param1.find(".html") == -1 else Path_Param1
        renderer = Path_Param1[0:Path_Param1.find(".html")] + "_main" # i.e.: 1stPathParam="ex" -> there is "ex.py"@routers dir (that's a module) -> Call it's "main" function.
        if renderer in options:
            select_func = (renderer, {"request":request, "payload":payload, "templates":templates, "db_query":db_query})
            return await options[select_func[0].replace("'", "")](*select_func[1].values())
        else: return templates.TemplateResponse(Path_Param1, {"request": request, "payload": payload})