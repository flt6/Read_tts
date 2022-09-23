from typing import Any
import consts

from requests.exceptions import RequestException
from json.decoder import JSONDecodeError
from traceback import extract_stack

from log import getLogger


class ServerError(Exception):
    def __init__(self, message: Any = None):
        '''
            @param message:
                text to print
        '''
        self.msg = str(message)


class AppError(ServerError):
    def __init__(self, message: Any = None):
        super().__init__(message)



class ErrorHandler:
    def __init__(
        self, err, src: str = "Unknown",
        logger=None, level: int = 1,
        exit=False, wait=False
    ):
        '''
            Dealing with errors.
            @param err:
                the error occurred.
                type: instance of Exception 
            @param src:
                the error occurred class name or function name.
            @param level:
                1: error
                2: critical
                3: exception
            @param exit:
                Whether exit the programm due to the error.
            @param wait:
                Whether wait when exit. (Only available when exit=True)
        '''
        if not isinstance(err, BaseException):
            raise TypeError(
                "param 'err' must be instance of 'BaseException', but {} got.".format(type(err)))
        if not(isinstance(level, int) and level < 4 and level > 0):
            raise ValueError(
                "param 'level' must be integer and between 1-3, but '{}' got.".format(level))

        if logger is None:
            lg = getLogger("ErrorHandler")
        else:
            lg = logger

        self.lgerr = lg.error
        self.lgcri = lg.critical
        self.lgexp = lg.exception
        self.lgdbg = lg.debug
        self.lgwar = lg.warning

        self.dbg = consts.DEBUG
        self.level = level
        self.err = err
        self.src = src
        self.exit = exit
        self.wait = wait
        self.call = False

    def show(self, message: Any):
        level = self.level
        for line in message.splitlines():
            line = f"{self.getStack()}: "+line
            if level == 1:
                self.lgerr(line)
            elif level == 2:
                self.lgcri(line)
            elif level == 3:
                self.lgexp(line, exc_info=True)
        if self.dbg:
            self.lgdbg('', exc_info=True)

    def getStack(self):
        st = extract_stack()
        return st[-4].name

    def quit(self):
        if self.exit:
            if self.wait:
                input("Pause (input enter to exit)")
            exit(1)
    
    def __del__(self):
        if not self.call:
            getLogger("ErrorHandler").error("ErrorHandler is initialized but not called.")
            getLogger("ErrorHandler").error(f"from: {self.src}")
            raise RuntimeWarning("ErrorHandler is initialized but not called.")

    def __call__(self):
        self.call = True
        err = self.err
        msg = ""
        if isinstance(err, AppError):
            msg = f"While getting data from APP, the server returned an error: {err.msg}"
        elif isinstance(err, ServerError):
            msg = int(err.msg)
            if msg == 404:
                msg = f"Server: 404 at {self.src}"
            else:
                msg = f"Server returned {err.msg} at {self.src}."
        elif isinstance(err, RequestException):
            msg = f"Network connecting error at {self.src}."
        elif isinstance(err, JSONDecodeError):
            msg = f"error occurred while decoding JSON at {self.src}:\n"
            msg += f"( {err.doc} ) {err.msg} at {err.pos}"
        elif isinstance(err, KeyboardInterrupt):
            msg = "KeyboardInterrupt!"
            self.exit = True
            self.wait = False
        elif isinstance(err, PermissionError):
            msg = "Permission denied!"
        elif isinstance(err, FileExistsError):
            msg = "File exists!"+err.args[0]
        else:
            msg = "Unknown error!"
            self.level = 2
            self.dbg = True
            # raise err
        self.show(msg)
        self.quit()
