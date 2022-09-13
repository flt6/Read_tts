from typing import Union,Optional
from log import Log
from model import Book, Chapter, ChapterList


def req(
    url: tuple[str,list[str]],
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
    def choose_book(self, books: list[Book]) -> tuple[int, int, Book]: ...
    def get_charpter_list(self, book: Book) -> Union[list[ChapterList],None]: ...
    def download_content(
        self, chapters: list[ChapterList]) -> tuple[list[Chapter], list[ChapterList]]: ...

    def _testIP(self, ip: str) -> bool: ...
