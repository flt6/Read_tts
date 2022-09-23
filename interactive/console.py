from requests import get
from utils import ConnectServer
from os import system
from re import search
import platform

def serverIP():
    global SERVER
    print("IP:")
    url = input(">>> ")
    bgn = search(r"^((http)|(https)):\/\/",url)
    port = search(r"(?<=(\:))\d+",url)
    if bgn is None:
        print("No http or https found. Auto added `http://`")
        url = "http://"+url
    if url[-1] == "/":
        print("Do not type '/' at the end of url. Auto removed.")
        url = url[:-1]
    if port is None:
        print("Port is not specified. If not 8080, please run modify again.")
        url = url + ":8080"
    
    with open("server_ip.conf","w") as f:
        f.write(url)
    SERVER = url

try:
    from exceptions import ErrorHandler
    from log import getLogger
    from utils import ToApp
    from consts import SERVER
    from main import main
except AssertionError:
    print("Server ip is not available!")
    serverIP()
    print("Please restart.")
    input("-------------------------------")
    exit(1)

help='''
Interactive command window for Read TTS
Now server ip: {}
Input number to choose function
===========run===========
----------basic----------
1. Start basic App
----------fix------------
2. Start with fix mode
3. Fix concat
--------settings---------
4. set ip
=========tools===========
---------cleanup---------
5. Clean server files
6. Clean local log files
----------check----------
7. Check ip config
8. Get log files from server

0. Exit
'''



def console_main():
    try:
        print(help.format(SERVER))
        try:
            mode=int(input(">>> "))
        except ValueError:
            print("Invalid input")
            return True
        print("----------------------------------------")

        if mode == "":
            print("Invalid input")
            return
        if mode == 1:
            # basic mode
            main(1)

        elif mode == 2:
            # fix mode
            main(2)

        elif mode == 3:
            # reconcat
            ser = ConnectServer
            ser.concat()
            ser.pack()
            print("Success")
            
        elif mode == 4:
            # set ip
            print("1. Server IP")
            print("2. APP IP")
            typ = int(input(">>> "))
            if typ == 1:
                serverIP()
            elif typ == 2:
                ToApp(ToApp.SAVEIP|ToApp.GETIP)

        elif mode == 5:
            # clean server
            get(SERVER+"/cleanup")
            print("Success")
            
        elif mode == 6:
            # clean local
            open("logs/debug.log","w").close()
            open("logs/info.log","w").close()
            open("logs/error.log","w").close()
            print("Success.")
            
        elif mode == 7:
            # check
            log = getLogger("Console")
            log.info("Start APP request test.")
            ToApp(ToApp.CHECKIP)
            log.info("Start Server test.")
            try:
                ret = get(SERVER+"/main/clean")
                if ret.status_code != 200:
                    print("Server test failed: %s" % ret.status_code)
                else:
                    log.info("Server test succeeded")
            except Exception as e:
                log.error("Server test failed: %s" % e)

        elif mode == 8:
            # get log file
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
        elif mode == 0:
            # exit
            return False
        else:
            print("Invalid input")
    except ConnectionRefusedError:
        getLogger("Console").error("Server is not available.")
        getLogger("Console").debug("Trace",exc_info=True)
    return True

if __name__ == '__main__':
    try:
        while console_main():
            input("-----------------------------\nPress Enter to continue.")
            if platform.system() == "Windows":
                system("cls")
            else:
                system("clear")
    except KeyboardInterrupt:
        exit(1)
    except Exception as e:
        ErrorHandler(e,"console")()
        
    