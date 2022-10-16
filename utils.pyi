from typing import Iterator, Optional, Union

from azure.cognitiveservices.speech.speech import ResultFuture

from log import Log
from model import Book, Chapter, ChapterList

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
    def init(self): ...

    def get_shelf(self) -> list[Book]: ...
    def choose_book(self, books: list[Book]) -> Book: ...

    def choose_area(self, book: Book) -> Iterator[int]: ...
    def choose_single(self) -> Iterator[int]: ...

    def get_charpter_list(self, book: Book) -> (list[ChapterList] | None): ...
    def download_content(
        self, chapters: list[ChapterList]) -> tuple[list[Chapter], list[ChapterList]]: ...

    def getIP(self) -> None: ...
    def saveIP(self) -> None: ...


class Trans:
    def __init__(self, type: Optional[int]): ...
    def content_basic(self, chap: Chapter) -> list[str]: ...
    def title(self, chap: Chapter) -> str: ...
    def __call__(self, chap: Chapter) -> list[Chapter]: ...


class ToServer:
    def __init__(self, optDir: str): ...
    def createdir(self) -> None: ...

    def callback(self, task: ResultFuture, j: int,
                 retry: set[Chapter], chapters: list[Chapter], bar): ...
    def asyncDownload(
        self, chapters: list[Chapter], max_task: Optional[int]) -> list[Chapter]: ...


def reConcat() -> None: ...
def merge(chapters: list[Chapter], dir: str,
          is_remove: Optional[bool]) -> None: ...


def time_fmt(time: float) -> str: ...
def redelete() -> None: ...
