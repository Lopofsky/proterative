from .helpers import do_some_stuff

async def main(request, payload, templates):
    if 'a_tag' not in payload['form_data']: a_tag = ""
    payload_new = await do_some_stuff.get_some_stuff(request, a_tag)
    payload_new.update(payload)
    #print("Through routers/index.py main(**)"+"\n"*3)
    return templates.TemplateResponse(payload_new['page_requested']+'.html', {"request": request, "payload": payload_new})