import logging
from os import path, mkdir


class Log(logging.Logger):
    def __init__(self, name, show=True, debug=False) -> None:
        '''Provide log function'''
        super().__init__(name, logging.DEBUG if debug else logging.INFO)
        self.isdebug = debug
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self.show = show
        self.gen_handle()
        self.register_handles()

    def debug(self,text,*args,**kwargs):
        if self.isEnabledFor(logging.DEBUG):
            if self.show:
                print("\033[1;37mDEBUG: "+str(text)+"\033[0m")
            self._log(logging.DEBUG,text,args,**kwargs)

    def info(self,text,*args,**kwargs):
        if self.isEnabledFor(logging.INFO):
            if self.show:
                print("\033[1;34mINFO: "+str(text)+"\033[0m")
            self._log(logging.INFO,text,args,**kwargs)

    def warning(self,text,*args,**kwargs):
        if self.isEnabledFor(logging.WARNING):
            if self.show:
                print("\033[1;32mWARNING: "+str(text)+"\033[0m")
            self._log(logging.WARNING,text,args,**kwargs)

    def error(self,text,*args,**kwargs):
        if self.isEnabledFor(logging.ERROR):
            if self.show:
                print("\033[1;31mERROR: "+str(text)+"\033[0m")
            self._log(logging.ERROR,text,args,**kwargs)

    def exception(self,text,*args,exc_info=True,**kwargs):
        self.error(text,*args,**kwargs,exc_info=exc_info)

    def critical(self,text,*args,**kwargs):
        if self.isEnabledFor(logging.CRITICAL):
            if self.show:
                print("\033[1;41mCRITICAL: "+str(text)+"\033[0m")
            self._log(logging.CRITICAL,text,args,**kwargs)

    def gen_handle(self) -> None:
        fmt = logging.Formatter("%(asctime)s - %(levelname)s - %(funcName)s: %(message)s")

        self.info_handle = logging.FileHandler("logs/info.txt")
        self.info_handle.setLevel(logging.INFO)
        self.info_handle.setFormatter(fmt)
        self.error_handle = logging.FileHandler("logs/error.txt")
        self.error_handle.setLevel(logging.ERROR)
        self.error_handle.setFormatter(fmt)
        if self.isdebug:
            self.debug_handle = logging.FileHandler("logs/debug.txt")
            self.debug_handle.setLevel(logging.DEBUG)
            self.debug_handle.setFormatter(fmt)

    def register_handles(self) -> None:
        self.addHandler(self.info_handle)
        self.addHandler(self.error_handle)
        if self.isdebug:
            self.addHandler(self.debug_handle)

    def get_logger(self) -> logging.Logger:
        return self

    def test(self):
        self.debug("Test")
        self.info("Test")
        self.error("Test")
        self.critical("Test")


if __name__ == '__main__':
    log = Log("Test",True,True)
    log.test()
