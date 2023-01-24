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
    def __init__(self, name) -> None:
        """Provide log function"""
        super().__init__(name, DEBUG if config.SHOW_DEBUG or config.SAVE_LOG else INFO)
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self._register_handles()

    def _register_handles(self) -> None:
        fmt = Formatter("%(asctime)s - %(levelname)8s - %(name)s: %(message)s")

        if config.SAVE_LOG:
            self._debug_handle = FileHandler("logs/debug.log")
            self._debug_handle.setLevel(DEBUG)
            self._debug_handle.setFormatter(fmt)
            self.addHandler(self._debug_handle)

        level = DEBUG if config.SHOW_DEBUG else INFO
        self.addHandler(RichHandler(
            level, rich_tracebacks=True, locals_max_string=20))

    def get_logger(self):
        return self


def getLogger(name: str = "Default") -> Log:
    return Log(
        name=name,
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
