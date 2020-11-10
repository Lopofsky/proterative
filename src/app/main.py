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

fs, module_2_import = "\\" if os_name == 'nt' else '/', "routers"
parent = dirname(realpath(__file__))
templates = Jinja2Templates(directory=parent+fs+"decoration"+fs+"templates")
app.mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static")
database_instance = Database()

@app.on_event("startup")
async def startup():
    await database_instance.connect()
    app.state.db = database_instance

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

async def get_query(r_obj, query_name):
    queries = {"test":"SELECT * FROM base"} # todo: Redis
    return [{k:v for k,v in item.items()} for item in await r_obj.fetch_rows(queries[query_name])]

@app.route("/", methods=["GET", "POST"])
@app.route("/{Path_Param1}/", methods=["GET", "POST"])
async def root(request: Request, Path_Param1: str='index'):
    payload = {"path":request.url.path}
    if payload["path"].strip(fs) != '': Path_Param1 = payload["path"].strip('/')
    path_exceptions = ['favicon.ico']
    #---------------- [START] DATABASE QUERIES FROM FORMS (?) ----------------
    query_name = "test"
    results = await get_query(r_obj=request.app.state.db, query_name=query_name)
    print("\n"*3, "results =", results, "\n"*3)
    #---------------- [END] DATABASE QUERIES FROM FORMS (?) ------------------
    if Path_Param1 in path_exceptions: pass
    else:
        if Path_Param1 == '': Path_Param1 = 'index'
        options = load_all(module_2_import)
        payload["page_requested"] = Path_Param1
        payload["form_data"] = await request.form() if "form" in dir(request) else None
        payload["path_params"] = request["path_params"] if "path_params" in dir(request) else None
        qp2s = str(request["query_string"].decode("utf-8")) # 'qp2s' aka "Query Parameters *to* String"
        payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2s.split("&")} if qp2s.find('=') > -1 and len(qp2s) >= 3 else None
        Path_Param1 = Path_Param1 + ".html" if Path_Param1.find(".html") == -1 else Path_Param1
        renderer = Path_Param1[0:Path_Param1.find(".html")] + "_main"
        if renderer in options:
            select_func = (renderer, {"request":request, "payload":payload, "templates":templates})
            return await options[select_func[0].replace("'", "")](*select_func[1].values())
        else: return templates.TemplateResponse(Path_Param1, {"request": request, "payload": payload})