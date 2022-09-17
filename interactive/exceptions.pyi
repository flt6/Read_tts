from typing import NoReturn, Optional, Union, Any
from log import Logger


class ServerError:
    def __init__(self, message: Optional[Any]): ...

class AppError(ServerError): ...


class ErrorHandler:
    def __init__(
        self, err, src: str,
        logger: Union[Logger, None] = None,
        level: int = 1,
        exit=False, wait=False
    ): ...

    def show(self, message: Any) -> None: ...
    def getStack(self) -> str: ...
    def quit(self) -> None: ...
    def __call__(self)-> Union[None,NoReturn]: ...
