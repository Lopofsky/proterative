from .helpers import do_some_stuff

async def main(request, payload, templates):
    a_tag = "" if 'a_tag' not in payload['form_data'] else payload['form_data']['a_tag']
    payload.update(await do_some_stuff.get_some_stuff(request, a_tag))
    return templates.TemplateResponse(payload['page_requested']+'.html', {"request": request, "payload": payload})