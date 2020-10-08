from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import ping, index
from os.path import dirname, basename, isfile, join, realpath
from os import chdir, getcwd, name as os_name
import glob
import importlib
import sys

app = FastAPI(debug=True)

sys.path.append(".")
parent = dirname(realpath(__file__))
if os_name == 'nt': fs = "\\"
else: fs = '/'
module_2_import = "routers"

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


templates = Jinja2Templates(directory=parent+fs+"decoration"+fs+"templates")
app.mount("/static/", StaticFiles(directory=parent+fs+"decoration"+fs+"static"), name="static")

@app.route("/", methods=["GET", "POST"])
@app.route("/{Path_Param1}/", methods=["GET", "POST"])
async def root(request: Request, Path_Param1: str='index'):
    payload = {"path":request.url.path}
    if payload["path"].strip(fs) != '': Path_Param1 = payload["path"].strip('/')
    path_exceptions = ['favicon.ico']
    if Path_Param1 in path_exceptions: pass
    else:
        if Path_Param1 == '': Path_Param1 = 'index'
        options = load_all(module_2_import)
        payload['page_requested'] = Path_Param1
        if 'form' in dir(request): payload["form_data"] = await request.form()
        else: payload["form_data"] = None
        if 'path_params' in dir(request): payload["path_params"] = request['path_params']
        else: payload["path_params"] = None
        # 'qp2s' aka "Query Parameters *to* String"
        qp2s = str(request['query_string'].decode("utf-8"))
        if qp2s.find('=') > -1 and len(qp2s) >= 3 : payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2s.split('&')}
        else: payload["query_params"] = None
        if Path_Param1.find('.html') == -1: Path_Param1 = Path_Param1+".html"
        renderer = Path_Param1[0:Path_Param1.find(".html")]+'_main'
        if renderer in options:
            select_func = (renderer, {"request":request, "payload":payload, "templates":templates})
            choice = options[select_func[0].replace("'", "")]
            result = choice(*select_func[1].values())
            return await result
        else: return templates.TemplateResponse(Path_Param1, {"request": request, "payload": payload})

#app.include_router(ping.router)
#app.include_router(home.router)