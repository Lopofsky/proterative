from datetime import datetime
from json import dumps, loads, JSONDecodeError
from uuid import uuid5, NAMESPACE_DNS
from collections import defaultdict as dd
from itertools import groupby
from operator import itemgetter
from typing import Union, List, Dict

try:
    from jinja2 import Markup
except ImportError:
    try:
        # Version 2.0.1
        from jinja2.utils import markupsafe
        Markup = markupsafe.Markup
    except ImportError:
        # Version 3.0.1
        from markupsafe import Markup


def merge_list(l1, l2):
    return l1 + l2


def pretty_json(dict_data):
    dumped_dict = dumps(
        dict_data,
        ensure_ascii=False,
        sort_keys=True,
        indent=4,
        separatores=(", ", ": "),
    )
    return Markup(f"<pre> {dumped_dict} </pre>")


def now(date_format=None):
    return datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S" 
        if date_format in (None, "") 
        else date_format
    )


def to_json(string):
    if string is None:
        return {}
    string = string.replace("\\", "").replace("'", '"')
    result = loads(string)
    if result == '{}':
        return {}
    return result


def get_uuid(dump):
    return uuid5(NAMESPACE_DNS, now())

#TODO: replace `dict2str` with `json_to_formatted_txt`
def dict2str(d: Union[str, Dict, None], function: str):
    string = ""

    if d is None:
        return string

    try:
        d = loads(d) if isinstance(d, str) else d
    except JSONDecodeError:
        raise Exception(f'{d=} is a str with non-valid JSON format!')
    
    if not isinstance(d, dict):
        raise Exception(f'{type(d)=} has to be of type (str, dict)')
    
    if function == "query_params":
        for k, v in d.items():
            temp = f'{str(k)}={str(v)}'
            temp = temp if string == "" else f"&{temp}"
            string += temp
    elif function == "beauty":
        for k, v in d.items():
            temp = f'{str(k)} -> {str(v)}'
            temp = temp if string == "" else Markup("</br>") + temp
            string += temp
    elif function == "2dict":
        string = d
    elif function == "keys":
        string = d
        string = string.keys()
    return string


def json_to_formatted_txt(
    payload: Union[str, Dict, None], 
    kv_sep: str=':', 
    group_sep: str=', '
):
    if payload is None:
        return None

    if isinstance(payload, str):
        try:
            payload = loads(payload)
        except JSONDecodeError as e:
            raise Exception(f'{type(payload)=} is a str with non-valid JSON format!')

    if not isinstance(payload, dict):
        raise Exception(f'{type(payload)=} has to be of type (str, dict)')

    result = group_sep.join([
        f'{k}{kv_sep}{v}'
        for k,v in payload.items()
    ])

    # if "<" in [group_sep, kv_sep]:
    #     result = Markup(result)

    return Markup(result)


def group_dict(
    data: Dict, 
    m_key: str, 
    side_k: List, 
    extra: List
):
    res, tmp_res = {}, []
    filtr = [m_key]
    items_of_interest = itemgetter(*side_k)
    for key, group in groupby(data, items_of_interest):
        d = dd(list)
        for thing in group:
            for k, v in thing.items():
                if k in filtr:
                    extra_dict = {x: thing[x] for x in extra}
                    d[k].append((v, extra_dict))
        tmp_res.append({key: d})
    for rec in tmp_res:
        for key in rec.keys():
            data = rec[key][m_key]
            if key in res:
                res[key][m_key].append(data)
            else:
                res[key] = {m_key: [data]}
    return res