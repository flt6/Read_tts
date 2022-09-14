from shutil import copy
from fastapi import FastAPI
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
compress_old:dict[str,Popen]=dict()
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
    delete("Output")
    mkdir("Output")
    for id in ids:
        dir=f"Output_{id}"
        for file in listdir(dir):
            copy(dir+"/"+file,"Output/")
        # delete(dir)

@app.get("/pack/start")
def pack_start():
    global compress
    cmd=[
        "7za",
        "a",
        f"opt",
        f"Output"
    ]
    pk = Popen(cmd,stdout=PIPE)
    compress=pk

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

@app.get("/cleanup")
def cleanup():
    l=listdir()
    for i in l:
        if search(r"(Output.+)|(opt.7z)",i) is not None:
            delete(i)

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