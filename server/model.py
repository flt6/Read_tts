from pydantic import BaseModel
from typing import Optional


class Book:
    author: str
    "作者"
    url: str
    "书籍网页"
    idx: int
    "当前章节数"
    title: str
    "当前章节名称"
    name: str
    "书名"
    tot: int

    def __init__(
            self, author: Optional[str] = None, bookUrl: Optional[str] = None,
            durChapterIndex: Optional[int] = None, durChapterTitle: Optional[str] = None,
            name: Optional[str] = None, totalChapterNum: Optional[int] = None, **kwargs) -> None:

        if None in [author, bookUrl, durChapterIndex, durChapterTitle, name, totalChapterNum]:
            self.available = False
            return
        else:
            self.available = True
            self.name = name           # type: ignore
            self.author = author       # type: ignore

            self.title = durChapterTitle  # type: ignore
            self.idx = durChapterIndex   # type: ignore
            self.tot = totalChapterNum   # type: ignore
            self.url = bookUrl           # type: ignore

            self.dict = kwargs


class ChapterList:

    idx: int
    '章节数'
    title: str
    '标题'
    url: str
    '章节链接'

    def __init__(self,  index: int, title: str, book: str, **kwargs) -> None:
        self.idx = index
        self.title = title
        self.url = book
        self.dict = kwargs



class ChapterModel(BaseModel):
    idx: int
    '章节数'
    title: str
    '标题'
    content: str
    '内容'


class Chapter:
    idx: int
    '章节数'
    title: str
    '标题'
    content: str
    '内容'

    def __init__(self, idx: int, title: str, content: str):
        self.idx = idx
        self.title = title
        self.content = content

    def __repr__(self):
        return "<Chapter idx={} title={} content={}>".format(self.idx, self.title, self.content.strip()[:5])
