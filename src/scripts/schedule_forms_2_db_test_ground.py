from datetime import timedelta as td
from datetime import datetime as dt

def simple_range(start, end, step, weekday=False):
    start, end = dt.strptime(start, '%Y-%m-%d'), dt.strptime(end, '%Y-%m-%d')
    step, day_names, result = td(days=step), ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday','Sunday'], []
    while start < end:
        t = start.strftime('%Y-%m-%d') if not weekday else (start.strftime('%Y-%m-%d'), day_names[start.weekday()])
        result.append(t)
        start += step
    return result

start, end, step = '2010-12-01', '2010-12-31', 1

date_range = simple_range(start, end, step, weekday=True)

f = {'scheduled_employee': '72', 'schedule_from': '2021-04-26', 'schedule_to': '2021-06-02', 'monday_1_from': '03:26', 'monday_1_to': '16:58', 'monday_2_from': '02:42', 'monday_2_to': '05:01', 'tuesday_1_from': '', 'tuesday_1_to': '', 'tuesday_2_from': '', 'tuesday_2_to': '', 'wednesday_1_from': '', 'wednesday_1_to': '', 'wednesday_2_from': '', 'wednesday_2_to': '', 'thursday_1_from': '', 'thursday_1_to': '', 'thursday_2_from': '', 'thursday_2_to': '', 'friday_1_from': '05:42', 'friday_1_to': '19:56', 'friday_2_from': '02:06', 'friday_2_to': '05:06', 'saturday_1_from': '', 'saturday_1_to': '', 'saturday_2_from': '', 'saturday_2_to': '', 'sunday_1_from': '', 'sunday_1_to': '', 'sunday_2_from': '', 'sunday_2_to': ''}
employee_ID = 72


db_res = defaultdict(dict)
for d in date_range:
    date, name, s = d[0], d[1].lower(), [1,2,3,4]
    schedule = {ii:f[name+'_'+str(ii)+'_from'] + '-' + f[name+'_'+str(ii)+'_to'] for ii in s if name+'_'+str(ii)+'_from' in f}
    if schedule[1] == '-': db_res[date] = {'day_off':employee_ID}
    else: db_res[date]['works'] = {employee_ID:schedule}
print("db_res ->", dict(db_res))