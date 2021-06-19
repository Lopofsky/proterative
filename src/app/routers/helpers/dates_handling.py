from datetime import timedelta as td
from datetime import datetime as dt

async def simple_range(start, end, step, weekday=False):
    start, end = dt.strptime(start, '%Y-%m-%d'), dt.strptime(end, '%Y-%m-%d')
    step, day_names, result = td(days=step), ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday','Sunday'], []
    while start < end:
        t = start.strftime('%Y-%m-%d') if not weekday else (start.strftime('%Y-%m-%d'), day_names[start.weekday()])
        result.append(t)
        start += step
    return result