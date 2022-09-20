from main import main
from requests import get
from exceptions import ErrorHandler
from consts import SERVER
from log import getLogger
from os import system
import platform

help='''
Interactive command window for Read TTS
Input number to choose function
1. Start basic App
2. Start with fix mode
3. Clean server files
4. Get log files from server
5. Clean local log files
6. Exit
'''
def console_main():
    try:
        print(help)
        mode=int(input(">>> "))
        print("----------------------------------------")

        if mode == "":
            print("Id not found")
            return
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
        elif mode == 6:
            return False
        else:
            print("`Mode` is invalid.")
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
        ErrorHandler(e,"console")
        
    