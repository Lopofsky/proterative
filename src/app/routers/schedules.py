from collections import defaultdict

from .helpers.dates_handling import simple_range

async def main(b_args):
    request, payload, render_template = b_args()
    #a_tag = "" if 'a_tag' not in payload['form_data'] else payload['form_data']['a_tag']
    #payload.update(await do_some_stuff.get_some_stuff(request, a_tag))
    if request.method == 'GET': return render_template(payload['page_requested']+'.html', {"request": request, "payload": payload})
    if request.method == 'POST':
        f = payload['form_data']
        start, end, employee_ID, step = f['schedule_from'], f['schedule_to'], f['scheduled_employee'], 1
        date_range = await simple_range(start, end, step, weekday=True)
        db_res = defaultdict(dict)
        for d in date_range:
            date, name, s = d[0], d[1].lower(), [1,2,3,4]
            schedule = {ii:{'from':f[name+'_'+str(ii)+'_from'], 'to':f[name+'_'+str(ii)+'_to']} for ii in s if name+'_'+str(ii)+'_from' in f}
            if schedule[1]['from'] == '': db_res[date] = {'day_off':employee_ID}
            else: db_res[date]['works'] = {employee_ID:schedule}
        #print("db_res ->", dict(db_res))