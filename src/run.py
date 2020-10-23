import uvicorn
from os import listdir, getcwd
from os.path import isfile, join
#from app.main import app

if __name__ == "__main__":
    #chdir("app")
    #print("CWD: ", getcwd())
    allfiles = [f for f in listdir(getcwd())] # if isfile(join(getcwd(), f))
    #print("all files(+dirs): ", allfiles)
    uvicorn.run("main:app", host="0.0.0.0", port=7000, reload=True, log_level="info")