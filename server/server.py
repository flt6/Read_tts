from traceback import format_exc
from log import getLogger
from shutil import copy
from fastapi import FastAPI,Body
from starlette.responses import FileResponse

from utils import delete
from model import Chapter,ChapterModel

from pickle import dumps,dump
import hashlib
from os import mkdir,listdir
from re import search
from subprocess import Popen,PIPE

from typing import Optional


app = FastAPI()
chaps:list[Chapter]=[]

deamons:dict[str,Popen]=dict()
progress:dict[str,list]=dict()
compress=None

@app.post("/main/chap")
def main_chap(file:ChapterModel):
    chaps.append(Chapter(file.idx,file.title,file.content))
    return {"msg":"Success"}

@app.get("/main/clean")
def main_clean():
    chaps.clear()

@app.get("/main/check")
def verify():
    md5=hashlib.md5()
    l=[(i.idx,i.title,i.content) for i in chaps]
    md5.update(dumps(l))
    return md5.hexdigest()

@app.get("/main/start")
async def main_start(type:int):
    global thr
    ver=verify()
    optDir = f"Output_{ver}"
    delete(optDir)
    delete(f"opt_{ver}.7z")
    with open(f"chap_{ver}.dmp","wb") as f:
        dump((chaps,optDir,type),f)
    cmd=[
        "python",
        "main.py",
        f"chap_{ver}.dmp"
    ]
    deamons.update({ver:Popen(cmd)})
    return ver

@app.get("/main/isalive")
def main_isalive(id:str):
    global deamons
    proc=deamons.get(id)
    if proc is None:
        return {"msg":"NotFound"}
    ret = proc.poll()
    if ret is None:
        return {"msg":"Running"}
    return {"msg":"Finished","code":ret}

# ------------------------------------------------

@app.get("/path/merge")
def pack_merge(ids:list[str]):
    try:
        delete("Output")
        mkdir("Output")
        for id in ids:
            dir=f"Output_{id}"
            for file in listdir(dir):
                copy(dir+"/"+file,"Output/")
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.get("/pack/start")
def pack_start():
    global compress
    try:
        redelete()
        cmd=[
            "7za",
            "a",
            f"opt",
            f"Output"
        ]
        pk = Popen(cmd,stdout=PIPE)
        compress=pk
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.get("/pack/available")
def pack_available():
    pk = compress
    if pk is None:
        return {"msg":"NotFound"}
    ret = pk.poll()
    if ret is None:
        return {"msg":"Running"}
    elif ret != 0:
        return {"msg":"Error","code":ret}
    return {"msg":"Available"}

@app.get("/pack/getfile")
def getfile():
    file = f"opt.7z"
    delete(f"Output")
    # print(file)
    return FileResponse(
        file,
        filename="Output.7z",
        # background=BackgroundTask(delete,file)
    )

# -------------------------------------------------------

@app.post("/progress/add")
def add_progress(num:int=Body(),uuid:str=Body()):
    global progress
    try:
        progress.update({uuid:[0,num,True]})
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.post("/progress/end")
def end_progress(uuid:str):
    global progress
    if uuid not in list(progress.keys()):
        return {"IsSuccess":False,"msg":"Progress `%s` not found"%uuid}
    progress[uuid][2]=False
    return {"IsSuccess":True}

@app.post("/progress/bar")
def update_progress(uuid:str):
    global progress
    if uuid not in list(progress.keys()):
        return {"IsSuccess":False,"msg":"Progress `%s` not found"%uuid}
    if not progress[uuid][2]:
        return {"IsSuccess":False,"msg":"Progress `%s` has closed"%uuid}
    progress[uuid][0]+=1
    return {"IsSuccess":True}

def check(l:list):
    if l[0]>l[1]:
        getLogger("progress").error("Out of total.")
        getLogger("progress").debug(str(l))
        return None
    return [l[0],l[1]]

@app.get("/progress/get")
def get_progress():
    l=list(progress.values())
    done=0
    tot=0
    for i in l:
        tem=check(i)
        if tem is None:
            continue
        done+=tem[0]
        tot+=tem[1]
    return done,tot

@app.get("/progress/reset")
def reset_progress():
    global progress
    try:
        progress.clear()
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.get("/progress/debug")
def debug():
    return progress

# -------------------------------------------------------

@app.get("/cleanup")
def cleanup():
    try:
        enum=["debug","info","error"]
        for file in enum:
            open(f"logs/{file}.log","w").close()
        l=listdir()
        for i in l:
            if search(r"(Output.*)|(opt.7z)",i) is not None:
                delete(i)
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.get("/redelete")
def redelete():
    try:
        l=listdir("Output")
        for i in l:
            if search(r"\s\(\d+\)\.mp3$",i) is not None:
                delete("Output/"+i)
        return {"IsSuccess":True}
    except Exception:
        return {"IsSuccess":False,"err":format_exc()}

@app.get("/log")
def log(typ:str, delete:Optional[bool]=True):
    if typ not in ["debug","info","error"]:
        return None
    with open(f"logs/{typ}.log","r",encoding="gb2312") as f:
        t=f.readlines()
    if delete:
        open(f"logs/{typ}.log","w").close()
    return t

# ---------------------------------------------------

# uvicorn server:app --host 0.0.0.0 --port 8080