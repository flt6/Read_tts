from main import main
from utils import ConnectServer
from requests import get
from consts import SERVER
from os import remove

help='''
Interactive command window for Read TTS
Input number to choose function
1. Start basic App
2. Start with fix mode
3. Clean server files
4. Get log files from server
5. Clean local log files
'''
print(help)
mode=int(input(">>> "))
print("----------------------------------------")
if mode == 1:
    main(1)
elif mode == 2:
    main(2)
elif mode == 3:
    get(SERVER+"/cleanup")
    print("Success")
elif mode == 4:
    print("Which level of log is needed to get?")
    print("Available:")
    print("debug(Default), info, error")
    level=input(">>> ")
    level = "debug" if level == "" else level

    print("Delete log file on server?")
    print("Available:")
    print("true(Default), false")
    delete=input(">>> ")
    delete = True if delete == "" else delete.lower()

    print("Save log file name")
    name=input(">>> ")

    if level not in ["debug", "info", "error"]:
        print("`Level`s is not available.")
    elif delete not in ["true","false"]:
        print("`Delete` is not available.")
    else:
        l=get(SERVER+"/log",params={"typ":level,"delete":delete}).json()
        with open(name+".log","w",encoding="utf-8") as f:
            f.writelines(l)
elif mode == 5:
    open("logs/debug.log","w").close()
    open("logs/info.log","w").close()
    open("logs/error.log","w").close()
    print("Success.")
else:
    print("`Mode` is invalid.")

input("--------------End------------\nPress Enter to exit")