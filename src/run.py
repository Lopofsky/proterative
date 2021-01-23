import uvicorn
#from os import listdir, getcwd
#from os.path import isfile, join

if __name__ == "__main__":
    #allfiles = [f for f in listdir(getcwd())]
    uvicorn.run("app.main:app", host="0.0.0.0", port=7000, reload=True, log_level="info")