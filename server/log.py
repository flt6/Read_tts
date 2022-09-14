from logging import Logger,Formatter,FileHandler
from logging import DEBUG,INFO,WARNING,ERROR,CRITICAL
from traceback import format_exc
from os import path, mkdir
import consts


class Log(Logger):
    def __init__(self, name, show=True, debug=False,show_dbg=True) -> None:
        '''Provide log function'''
        super().__init__(name, DEBUG if debug else INFO)
        self.isdebug = debug
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self.show = show
        self.show_dbg=show_dbg
        self.super=super()
        self.gen_handle()
        self.register_handles()

    def debug(self, text, *args, exc_info=None, **kwargs):
        if self.isEnabledFor(DEBUG):
            if self.show and self.show_dbg:
                print(self._fmt(f"DEBUG: {str(text)}", DEBUG))
            self._log(DEBUG, text, args, exc_info=exc_info, **kwargs)

    def info(self, text, *args, exc_info=None, **kwargs):
        if self.isEnabledFor(INFO):
            if self.show:
                print(self._fmt(f"INFO: {str(text)}", INFO))
            self._log(INFO, text, args, exc_info=exc_info, **kwargs)

    def warning(self, text, *args, exc_info=None, **kwargs):
        if self.isEnabledFor(WARNING):
            if self.show:
                print(self._fmt(f"WARNING: {str(text)}", WARNING))
            self._log(WARNING, text, args, exc_info=exc_info, **kwargs)

    def error(self, text, *args, exc_info=None, **kwargs):
        if self.isEnabledFor(ERROR):
            if self.show:
                print(self._fmt(f"ERROR: {str(text)}", ERROR))
            self._log(ERROR, text, args, exc_info=exc_info, **kwargs)

    def exception(self, text, *args, exc_info=True, **kwargs):
        self.error(text, *args, exc_info=exc_info, **kwargs)

    def critical(self, text, *args, exc_info=None, **kwargs):
        if self.isEnabledFor(CRITICAL):
            if self.show:
                print(self._fmt(f"CRITICAL: {str(text)}", CRITICAL))
            self._log(CRITICAL, text, args,
                      exc_info=exc_info, **kwargs)

    def _log(self, level, msg, args, exc_info=None, extra=None, stack_info=False, stacklevel=1):
        super()._log(level, msg, args, None, extra, stack_info, stacklevel)
        if exc_info:
            print(self._fmt(format_exc(), level))
            for line in format_exc().splitlines():
                super()._log(ERROR, line, args, None, extra, stack_info, stacklevel)

    def _fmt(self, text, level):
        d = {
            DEBUG:    "\033[1;37m",
            INFO:     "\033[1;34m",
            WARNING:  "\033[1;32m",
            ERROR:    "\033[1;31m",
            CRITICAL: "\033[1;41m"
        }
        return d[level]+text+"\033[0m"

    def gen_handle(self) -> None:
        # fmt = Formatter("%(asctime)s - %(levelname)s - %(funcName)s: %(message)s")
        fmt = Formatter(
            "%(asctime)s - %(levelname)8s - %(name)s: %(message)s")

        self.info_handle = FileHandler("logs/info.log")
        self.info_handle.setLevel(INFO)
        self.info_handle.setFormatter(fmt)
        self.error_handle = FileHandler("logs/error.log")
        self.error_handle.setLevel(ERROR)
        self.error_handle.setFormatter(fmt)
        if self.isdebug:
            self.debug_handle = FileHandler("logs/debug.log")
            self.debug_handle.setLevel(DEBUG)
            self.debug_handle.setFormatter(fmt)

    def register_handles(self) -> None:
        self.addHandler(self.info_handle)
        self.addHandler(self.error_handle)
        if self.isdebug:
            self.addHandler(self.debug_handle)

    def get_logger(self):
        return self


def getLogger(name: str = "Default") -> Log:
    return Log(name=name, show=consts.TO_CONSOLE, debug=consts.DEBUG,show_dbg=consts.SHOW_DBG).get_logger()
