from logging import (
    DEBUG,
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
        super().__init__(name, DEBUG)
        if not path.exists("logs"):
            mkdir("logs")
        elif not path.isdir("logs"):
            raise FileExistsError(
                "There is a file named 'logs', which is the same as the log directory."
            )
        self._register_handles()

    def _register_handles(self) -> None:
        fmt = Formatter("%(asctime)s - %(levelname)8s - %(name)s: %(message)s")

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
