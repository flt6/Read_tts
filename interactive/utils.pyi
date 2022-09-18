from requests import Response
from typing import Any, Union, Optional
from model import Book, Chapter, ChapterList
from log import Log


def req(
    url: tuple[str, list[str]],
    caller: str,
    logger: Optional[Log],
    level: Optional[int],
    exit: Optional[bool],
    wait: Optional[bool]
) -> Union[dict, None]: ...


class ToApp:
    logger: Log
    ip: str

    def __init__(self): ...
    def get_shelf(self) -> list[Book]: ...
    def choose_book(self, books: list[Book]) -> Book: ...
    def choose_area(self, book: Book): ...
    def choose_single(self, book: Book): ...

    def get_charpter_list(
        self, book: Book) -> Union[list[ChapterList], None]: ...
    def download_content(
        self, chapters: list[ChapterList]) -> tuple[list[Chapter], list[ChapterList]]: ...

    def getIP(self) -> None: ...
    def saveIP(self) -> None: ...


class ConnectServer:
    # consts
    FINISHED: int
    RUN_ERROR: int
    NOT_FOUND: int
    RUNNING: int

    # useful method
    @classmethod
    def check(cls, ret: Response) -> Union[dict[str, Any], str, list[str]]: ...

    # main
    @classmethod
    def chap(cls, ch: Chapter) -> None: ...
    @classmethod
    def main_start(cls, type: int) -> Union[str,None]: ...
    @classmethod
    def main_clean(cls) -> None: ...
    @classmethod
    def verify(cls, ch: list[Chapter]) -> bool: ...
    @classmethod
    def main_isalive(cls, id: str) -> Union[int, None]: ...

    # progress
    @classmethod
    def init(cls) -> None: ...

    @classmethod
    def get_retry(cls) -> list[Chapter]: ...

    # failed
    @classmethod
    def get_fail(cls) -> tuple[int,list[str]]: ...

    # tools
    @classmethod
    def pack(cls, id: list[str]): ...
    @classmethod
    def progress(cls): ...
    @classmethod
    def clean(cls): ...
