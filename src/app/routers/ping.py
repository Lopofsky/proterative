from fastapi import APIRouter, Request

router = APIRouter()

@router.get("/ping/")
@router.get("/ping/{Pente}/")
@router.get("/ping/{Pente}/{Dodeka}/")
async def pong(Pente: str = '', Dodeka: int = 0, test1: int = 0, test2: int = 0):
    PDBD = {"Pente":{"a":5*12, "b":5*2, "c":5*1, "d":5*0, "f":5*5}}
    response = {}
    trigger = 0
    input_control = lambda pente,t1,t2: 'no (Path+Query)' if t1==t2==0 and pente=='' else ('Only Query' if pente=='' and t1!=t2 else ('Only Path' if pente!='' and t1==t2==0 else 'Both (Path+Query)'))
    input_analysis = input_control(Pente, test1, test2)
    if input_analysis in ('Only Path', 'Both (Path+Query)') and Pente not in PDBD["Pente"]:
        return {"error!":"username '"+str(Pente)+"' doesn't exist!"}
    defacto_endfix = {"your math":str(test1*test2)}
    if input_analysis == 'no (Path+Query)':
        result = {"error!":"whatever data man..."}
    if input_analysis == 'Only Query':
        result = {"Query":{'test1':test1, 'test2':test2}}
        result.update(defacto_endfix)
    if input_analysis == 'Only Path':
        trigger = 1
        result = {"User":Pente, "Pente-ness":PDBD["Pente"][Pente]}
    if input_analysis == 'Both (Path+Query)':
        trigger = 1
        result = {"User":Pente, "Pente-ness":PDBD["Pente"][Pente]}
        result.update(defacto_endfix)
    if trigger == 1:
        if Dodeka > 0:
            result.update({"Your Dodeka-ness":PDBD['Pente'][Pente]*Dodeka})
        else:
            pass
    return result