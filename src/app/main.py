from fastapi import FastAPI, Depends, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from app.routers import ping, index
import os 

parent = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=parent+"/decoration/templates")

app = FastAPI(debug=True)
app.mount("/static/", StaticFiles(directory=parent+"/decoration/static"), name="static")

@app.route("/", methods=["GET", "POST"])
@app.route("/{Path_Param1}/", methods=["GET", "POST"])
async def root(request: Request, Path_Param1: str='index'):
    payload = {"path":request.url.path}
    if payload["path"].strip('/') != '':
        Path_Param1 = payload["path"].strip('/')
    path_exceptions = ['favicon.ico']
    if Path_Param1 in path_exceptions:
        pass
    else:
        payload['page_requested'] = Path_Param1
        if 'form' in dir(request):
            payload["form_data"] = await request.form()
        else:
            payload["form_data"] = None
        if 'path_params' in dir(request):
            payload["path_params"] = request['path_params']
        else:
            payload["path_params"] = None
        qp2s = str(request['query_string'].decode("utf-8"))
        if qp2s.find('=') > -1 and len(qp2s) >= 3 :
            payload["query_params"] = {z.split('=')[0]:z.split('=')[1] for z in qp2s.split('&')}
        else:
            payload["query_params"] = None
        if Path_Param1.find('.html') == -1:
            renderer = Path_Param1+'.main(request, payload, templates)'
            Path_Param1 = Path_Param1+".html"
        else:
            renderer = Path_Param1+'.main(request, payload, templates)'
            Path_Param1 = Path_Param1[0:Path_Param1.find(".html")]
        try:
            return await eval(renderer)
        except:
            print("\n\n Path_Param1, renderer, payload ==", Path_Param1, renderer, payload, "\n\n")
            return templates.TemplateResponse(Path_Param1, {"request": request, "payload": payload})

#app.include_router(ping.router)
#app.include_router(home.router)