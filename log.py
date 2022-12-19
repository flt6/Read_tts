from logging import (
    DEBUG,
    ERROR,
    INFO,
    FileHandler,
    Formatter,
    Logger,
)
from rich.logging import RichHandler
from os import mkdir, path

import config


class Log(Logger):
    def __init__(self, name, show=True, debug=False) -> None:
        """Provide log function"""
        super().__init__(name, DEBUG if debug else INFO)
        self.isdebug = debug
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self.show = show
        self.super = super()
        self.gen_handle()
        self.register_handles()

    def gen_handle(self) -> None:
        fmt = Formatter("%(asctime)s - %(levelname)8s - %(name)s: %(message)s")

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
        if self.show:
            self.addHandler(RichHandler(
                rich_tracebacks=True, locals_max_string=50))

    def get_logger(self):
        return self


def getLogger(name: str = "Default") -> Log:
    return Log(
        name=name,
        show=config.TO_CONSOLE,
        debug=config.DEBUG,
    ).get_logger()


def test():
    log = getLogger("test")
    log.debug("1" * 20)
    log.info("2" * 50)
    try:
        1 / 0
    except ZeroDivisionError:
        log.exception("5" * 50)
    log.critical("23q" * 80)


if __name__ == "__main__":
    test()
