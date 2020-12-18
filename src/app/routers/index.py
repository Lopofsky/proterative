from .helpers import do_some_stuff

async def main(request, payload, templates, db_query):
    a_tag = "" if 'a_tag' not in payload['form_data'] else payload['form_data']['a_tag']
    query = "test" if 'query_name' not in payload['form_data'] else payload['form_data']['query_name']
    payload_new = await do_some_stuff.get_some_stuff(request, a_tag)
    payload_new.update(payload)
    #print("Through routers/index.py main(**)"+"\n"*1)
    #---------------- [START] DATABASE QUERIES FROM FORMS (?) ----------------
    payload_new["DB Data"] = await db_query(r_obj=request.app.state.db, query_name=query)
    #---------------- [END] DATABASE QUERIES FROM FORMS (?) ------------------
    return templates.TemplateResponse(payload_new['page_requested']+'.html', {"request": request, "payload": payload_new})