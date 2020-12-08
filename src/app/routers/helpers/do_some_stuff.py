async def get_some_stuff(request, a_tag):
    if a_tag == "": return {"a_tag":"init it", "tag_1":1, "tag_2":{"one":[1,2,3], "two":[2,3,4], "three":[3,4,5], "four":[4,5,6], "five":[5,6,7]}, "tag_3":"some_other_text"}
    else: return {}