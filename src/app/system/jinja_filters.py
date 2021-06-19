from jinja2 import Markup
from datetime import datetime
import json, uuid

def merge_list(l1, l2): return l1+l2
def pretty_json(dict_data): return Markup("<pre>"+json.dumps(dict_data, sort_keys=True, indent=4, separators=(', ', ': '))+"</pre>")
def get_uuid(dump): return uuid.uuid5(uuid.NAMESPACE_DNS, now())
def now(date_format=None): return datetime.now().strftime("%Y-%m-%d %H:%M:%S" if date_format in (None, '') else date_format)
def to_json(string): return json.loads(string.replace('\\', '').replace("'", '"')) if string is not None else "None"

def dict2q(d, function):
    string = ''
    if function == 'query_params':
        for k,v in d.items():
            temp = str(k)+'='+str(v)
            temp = temp if string == '' else '&'+temp
            string += temp
    elif function == 'beauty':
        d = json.loads(d) if type(d)==str else d
        for k,v in d.items():
            temp = str(k)+' -> '+str(v)
            temp = temp if string == '' else Markup("</br>")+temp
            string += temp
    elif function == '2dict':
        string = json.loads(d) if type(d)==str else d
    elif function == 'keys':
        string = json.loads(d) if type(d)==str else d
        string = string.keys()
    return string

def group_dict(data, m_key, side_k, extra):
    import itertools, collections, operator
    res, tmp_res = {}, []
    filtr = [m_key]
    items_of_interest = operator.itemgetter(*side_k)
    for key, group in itertools.groupby(data, items_of_interest):
        d = collections.defaultdict(list)
        for thing in group:
            for k, v in thing.items():
                if k in filtr:
                    extra_dict = {x:thing[x] for x in extra}
                    d[k].append((v, extra_dict))
        tmp_res.append({key:d})
    for rec in tmp_res:
        for key in rec.keys():
            data = rec[key][m_key]
            if key in res: res[key][m_key].append(data)
            else: res[key] = {m_key:[data]}
    return res