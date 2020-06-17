from .helpers import do_some_stuff

async def main(request, payload_0, templates):
    if 'a_tag' not in payload_0['form_data']:
        a_tag = ""
    payload = await do_some_stuff.get_some_stuff(request, a_tag)
    payload.update(payload_0)
    print("\n\n", payload, "\n\n")
    return templates.TemplateResponse(payload['page_requested']+'.html', {"request": request, "payload": payload})