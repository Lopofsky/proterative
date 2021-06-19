from datetime import datetime as dt, timedelta as td
import json

year = dt.now().year
table_name = "Schedule" + str(year)
daterange = {k:dt.strptime(str(year) + v, '%Y-%m-%d').date() for k,v in {'start':'-01-01', 'end':'-12-31'}.items()}
date_list = [dt.strftime(daterange['start'] + td(days=x), '%Y-%m-%d') for x in range((daterange['end'] - daterange['start']).days + 1)]
#print(date_list)

to_db = json.dumps({date:{} for date in date_list})
print(to_db)
