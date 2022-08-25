from typing import Any, Union,Optional
from log import Log
from model import Book, Chapter, ChapterList
from asyncio import Task


def req(
    url: str,
    caller: str,
    logger: Optional[Log],
    level: Optional[int],
    exit: Optional[bool],
    wait: Optional[bool]
) -> Union[dict, None]: ...


class Stack:
    def __init__(self): ...
    def push(self, x: Any) -> None: ...
    def top(self) -> Any: ...
    def pop(self) -> Any: ...
    def length(self) -> int: ...
    def empty(self) -> bool: ...


class ToApp:
    logger: Log
    ip: str

    def __init__(self): ...
    def get_shelf(self) -> list[Book]: ...
    def choose_book(self, books: list[Book]) -> tuple[int, int, Book]: ...
    def get_charpter_list(self, book: Book) -> list[ChapterList]: ...
    def download_content(
        self, chapters: list[ChapterList]) -> tuple[list[Chapter], list[ChapterList]]: ...

    def _testIP(self, ip: str) -> bool: ...


class Trans:
    def __init__(self, type: int): ...
    def content_basic(self, chap: Chapter) -> Chapter: ...
    def title(self, chap: Chapter) -> Chapter: ...
    def __call__(self, chap: Chapter) -> Chapter: ...


class ToServer:
    def __init__(self, optDir: str): ...
    def createdir(self) -> None: ...
    def asyncDownload(self, chapters: list[Chapter]) -> list[Chapter]: ...
