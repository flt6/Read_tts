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
        self._isdebug = debug
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self._show = show
        self._gen_handle()
        self._register_handles()

    def _gen_handle(self) -> None:
        fmt = Formatter("%(asctime)s - %(levelname)8s - %(name)s: %(message)s")

        self._info_handle = FileHandler("logs/info.log")
        self._info_handle.setLevel(INFO)
        self._info_handle.setFormatter(fmt)
        self._error_handle = FileHandler("logs/error.log")
        self._error_handle.setLevel(ERROR)
        self._error_handle.setFormatter(fmt)
        if self._isdebug:
            self._debug_handle = FileHandler("logs/debug.log")
            self._debug_handle.setLevel(DEBUG)
            self._debug_handle.setFormatter(fmt)

    def _register_handles(self) -> None:
        self.addHandler(self._info_handle)
        self.addHandler(self._error_handle)
        if self._isdebug:
            self.addHandler(self._debug_handle)
        if self._show:
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
