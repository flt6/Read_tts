from requests import get
from log import getLogger
from os.path import isfile,isdir
from re import match

from exceptions import ErrorHandler
from exceptions import ServerError, RequestException

import consts
from typing import Any, Union


class ToApp:
    def __init__(self):
        self.logger = getLogger("ToApp")
        self.getIP()
        self.saveIP()

    def get_shelf(self) -> bool:
        '''
            Get the shelf infomation from the app.
            @return: Is succeeded.
        '''
        try:
            res = get(consts.GET_SHELF.format(self.ip))
            if res.status_code != 200:
                raise ServerError(1, res.status_code)
        except Exception as e:
            ErrorHandler(e, "ToApp")()
        try:
            shelf = res.json()["data"]
        except Exception as e:
            ErrorHandler(e, "ToApp")()

    def _testIP(self, ip: str):
        if not match("(\d{1,3}\.){3}\d{1,3}",ip):
            self.logger.debug("Regular Expression match failed.")
            return False
        try:
            res = get(consts.GET_SHELF.format(ip))
            self.logger.debug("HTTP connect status_code=%d" % res.status_code)
            if res.status_code != 200:
                raise ServerError(1, res.status_code)
            return True
        except RequestException:
            self.logger.debug("Can't connect to server")
            return False
        except Exception as e:
            ErrorHandler(e, "testIP", self.logger, 2)()

    def getIP(self):
        if isfile("ip.conf"):
            try:
                with open("ip.conf", "r") as f:
                    ip = f.read()
                    self.logger.debug("Set ip=%s" % ip)
            except Exception as e:
                ErrorHandler(e, "ToApp", self.logger)()
            if self._testIP(ip):
                self.ip = ip
                return
            self.logger.debug("_testIP() returned False")
        while True:
            ip = input("ip: ")
            self.logger.debug("Set ip=%s" % ip)
            if ":" not in ip:
                ip += ":1122"
            if self._testIP(ip):
                self.ip = ip
                return
            else:
                self.logger.debug("_testIP() returned False")
                print("Can't connect to APP.")
    def saveIP(self):
        if isdir("ip.conf"):
            print("Directory 'ip.conf' already exists.")
            print("Please delete it first, or IP can't be saved.")
            e=FileExistsError("Directory 'ip.conf' exists.")
            ErrorHandler(e, "ToApp")()
            return
        try:
            f=open("ip.conf", "w")
            f.write(self.ip)
        except Exception as e:
            ErrorHandler(e, "ToApp")()
        finally:
            f.close()
        

def test():
    app = ToApp()
    app.get_shelf()


if __name__ == '__main__':
    print(test())
