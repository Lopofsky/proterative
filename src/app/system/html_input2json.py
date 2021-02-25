from starlette.datastructures import UploadFile
import json, asyncio

async def merge(a, b, path=None):
    #"merges b into a"
    if path is None: path = []
    for key in b:
        if key in a:
            if isinstance(a[key], dict) and isinstance(b[key], dict): await merge(a[key], b[key], path + [str(key)])
            else: 
                if type(a[key]) == str: a[key] = [a[key], b[key]]
                elif type(a[key]) == list: a[key].append(b[key])
                else: raise Exception("key >"+key+"< with value >"+str(value)+"< is of type "+type(a[key])+" - Not Supported!")
        else: a[key] = b[key]
    return a

async def create_list_of_dicts_from_html_form(da_form, prefix, input_name_str_exception):
    records = []
    for k, v in da_form.items():
        v = {v.filename:{"filetype":v.content_type, "tempfile":v.file}} if type(v)==UploadFile else v
        is_exception = False if input_name_str_exception is None else k.find(input_name_str_exception) > -1
        if k.startswith(prefix) and not is_exception:
            t_res = k.split('.')[1:]
            main_k = k[1:].split('.')[0]
            res = {}
            for dict_key in enumerate(reversed(t_res)):
                key = dict_key[1]
                try: value = json.loads(v.replace("'", '"'))
                except: value = v
                if dict_key[0] == 0: res = {key:value}
                else: res = {key:res}
            records.append({main_k:res})
        else: records.append({k.replace(prefix, ""):v})
    return records

async def make_dict_from_dotted_string(da_form, prefix="*", input_name_str_exception=None):
    records = await create_list_of_dicts_from_html_form(da_form, prefix, input_name_str_exception)
    fin_dict = {}
    for a in records:
        fin_dict = await merge(fin_dict, a)
    return fin_dict

async def get_single_value_from_dict(data):
    async def the_essence(data):
        if data is not None:
            for k,v in data.items():
                if type(v) != dict:
                    yield {k:v}
                    await asyncio.sleep(1)
                else: 
                    yield await the_essence(v)
                    await asyncio.sleep(1)
            return 
        else: return 
    results = [k for k in await the_essence(data)]
    return results

async def float_any(s):
    s = str(s).strip()
    return float(s) if s else 0.0