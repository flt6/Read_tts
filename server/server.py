from fastapi import FastAPI
from starlette.responses import FileResponse

from utils import delete
from model import Chapter

from pickle import dumps,dump
import hashlib
from subprocess import Popen,PIPE

from typing import Optional


app = FastAPI()
chaps:list[Chapter]=[]

deamons:dict[str,Popen]=dict()
compress:dict[str,Popen]=dict()

@app.post("/main/chap")
def main_chap(file:Chapter):
    chaps.append(Chapter(file.idx,file.title,file.content))
    return {"msg":"Success"}

@app.get("/main/check")
def verify():
    md5=hashlib.md5()
    l=[(i.idx,i.title,i.content) for i in chaps]
    md5.update(dumps(l))
    return md5.hexdigest()


@app.get("/main/start")
async def main_start(optDir:str,type:int):
    global thr
    ver=verify()
    delete(f"Output_{ver}")
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

@app.get("/log")
def log(typ:str, delete:Optional[bool]=True):
    if typ not in ["debug","info","error"]:
        return None
    with open(f"logs/{typ}.log","r",encoding="utf-8") as f:
        t=f.readlines()
    if delete:
        open(f"logs/{typ}.log","w").close()
    return t

@app.get("/pack/start")
def pack_start(id:str):
    cmd=[
        "7za",
        "a",
        f"opt_{id}",
        f"Output_{id}"
    ]
    pk = Popen(cmd,stdout=PIPE)
    compress.update({id:pk})

@app.get("/pack/available")
def pack_available(id:str):
    pk = compress.get(id)
    if pk is None:
        return {"msg":"NotFound"}
    ret = pk.poll()
    if ret is None:
        return {"msg":"Running"}
    elif ret != 0:
        return {"msg":"Error","code":ret}
    return {"msg":"Available"}

@app.get("/pack/getfile")
def getfile(id:str):
    if pack_available(id)["msg"] != "Available":
        return {"msg":"NotAvailable"}
    return FileResponse(
        f"opt_{id}.7z",
    )
