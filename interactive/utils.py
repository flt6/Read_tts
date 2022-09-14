from alive_progress import alive_bar
from requests.utils import quote  # type: ignore
from requests import get, post
from os.path import isfile, isdir
from pickle import dumps

from re import match

from consts import SERVER as SER
from model import Book, ChapterList, Chapter
from log import getLogger

from requests.exceptions import RequestException
from exceptions import ErrorHandler
from exceptions import ServerError, AppError

from requests import Response
from typing import Any, Union

import consts
import hashlib
import json


def req(param, caller="Requester", logger=None,
        level=1, exit=False, wait=False):
    try:
        url, args = param
        url = url.format(args[0], *[quote(str(i)) for i in args[1:]])
        getLogger("request").debug("url=%s,caller=%s" % (url, caller))
        res = get(url)
        if res.status_code != 200:
            raise ServerError(res.status_code)  # type: ignore
    except Exception as e:
        ErrorHandler(e, caller, logger, level, exit, wait)()
        return None
    try:
        json = res.json()
        if json["isSuccess"] == False:
            raise AppError(json["errorMsg"])  # type: ignore
        json = json["data"]
    except Exception as e:
        ErrorHandler(e, caller, logger, level, exit, wait)()
        return None
    return json


class ToApp:
    def __init__(self):
        self.logger = getLogger("ToApp")
        self.getIP()
        self.saveIP()

    def get_shelf(self):
        '''
            Get the shelf infomation from the app.
            @return: Is succeeded.
        '''
        url = consts.GET_SHELF
        shelf: dict = req((url, [self.ip]), 'ToApp',
                          level=2, exit=True, wait=True)  # type: ignore
        books = []
        for i in range(len(shelf)):
            book = Book(**shelf[i])
            if not book.available:
                self.logger.debug("Book not available")
                continue
            if book.idx == 0:
                self.logger.debug(f"No ChaperIndex.")
                # continue
            tip = consts.CHOOSEBOOK % (
                i+1,
                book.name,
                book.author,
                book.idx
            )
            print(tip)
            books.append(book)
        return books

    def choose_book(self, books: list[Book]):
        num = int(input("No. "))-1
        bgn = input(
            "From(%d: %s): " % (
                books[num].idx,
                books[num].title
            )
        )
        bgn = books[num].idx if bgn == '' else int(bgn)
        to = int(input("To. "))
        book = books[num]
        return (bgn, to, book)

    def get_charpter_list(self, book: Book):
        url = consts.GET_CHAPTER_LIST
        chapters = req((url, [self.ip, book.url]),
                       "ToApp", level=2, exit=True, wait=True)
        if chapters is None:
            return
        return [ChapterList(**item, book=book.url) for item in chapters]

    def download_content(self, chapters: list[ChapterList]):
        retry = []
        con = []
        with alive_bar(len(chapters)) as bar:
            for ch in chapters:
                url = consts.GET_CONTENT
                res = req((url, [self.ip, ch.url, ch.idx]), "ToApp")
                bar()
                if res is None:
                    retry.append(ch)
                    continue
                con.append(Chapter(ch.idx, ch.title, res))
        return (con, retry)

    def _testIP(self, ip: str):
        if not match(r"(\d{1,3}\.){3}\d{1,3}", ip):
            self.logger.debug("Regular Expression match failed.")
            return False
        try:
            res = get(consts.GET_SHELF.format(ip))
            self.logger.debug("HTTP connect status_code=%d" % res.status_code)
            if res.status_code != 200:
                raise ServerError(res.status_code)  # type: ignore
            return True
        except RequestException:
            self.logger.debug("Can't connect to server")
            return False
        except Exception as e:
            ErrorHandler(e, "testIP", self.logger, 2)()

    def getIP(self):
        if isfile("ip.conf"):
            try:
                with open("ip.conf", "r") as f:
                    ip = f.read()
                    self.logger.debug("Set ip=%s" % ip)
                    if self._testIP(ip):
                        self.ip = ip
                        return
            except Exception as e:
                ErrorHandler(e, "ToApp", self.logger)()
            self.logger.debug("_testIP() returned False")
        while True:
            ip = input("ip: ")
            self.logger.debug("Set ip=%s" % ip)
            if ":" not in ip:
                ip += ":1122"
            if self._testIP(ip):
                self.ip = ip
                return
            else:
                self.logger.debug("_testIP() returned False")
                print("Can't connect to APP.")

    def saveIP(self):
        if isdir("ip.conf"):
            print("Directory 'ip.conf' already exists.")
            print("Please delete it first, or IP can't be saved.")
            e = FileExistsError("Directory 'ip.conf' exists.")
            ErrorHandler(e, "ToApp")()
            return
        try:
            with open("ip.conf", "w") as f:
                f.write(self.ip)
        except Exception as e:
            ErrorHandler(e, "ToApp")()


class ConnectServer:

    FINISHED = 1
    RUN_ERROR = 2
    NOT_FOUND = 3
    RUNNING = 4

    @classmethod
    def check(cls, ret: Response) -> Union[dict[str, Any], str, list[str]]:
        getLogger("SerReq").debug("url=%s text=%s" % (ret.url, ret.text))
        if ret.status_code != 200:
            e = ServerError("status_code = %d" % ret.status_code)
            ErrorHandler(e, "Server", exit=True, wait=True)
        return ret.json()

    @classmethod
    def chap(cls, ch: Chapter) -> None:
        d = ch.get_dict()
        ret = post(SER+"/main/chap", json=d)
        ret = cls.check(ret)
        assert isinstance(ret, dict)
        assert ret["msg"] == "Success"

    @classmethod
    def main_start(cls, type: int) -> str:
        ret = get(SER+"/main/start", params={"type": type})
        ret = cls.check(ret)
        assert isinstance(ret, str)
        return ret

    @classmethod
    def main_clean(cls) -> None:
        cls.check(get(SER+"/main/clean"))

    @classmethod
    def verify(cls, ch: list[Chapter]) -> bool:
        ser = cls.check(get(SER+"/main/check"))
        assert isinstance(ser, str)
        md5 = hashlib.md5()
        l = [(i.idx, i.title, i.content) for i in ch]
        md5.update(dumps(l))
        return md5.hexdigest() == ser

    @classmethod
    def main_isalive(cls, id: str) -> Union[int, None]:
        ret = cls.check(get(SER+"/main/isalive", params={"id": id}))
        assert isinstance(ret, dict)
        msg = ret["msg"]
        if msg == "Finished":
            if ret["code"] == 0:
                return cls.FINISHED
            else:
                getLogger("Server").error(
                    "run failed with return code %d" % ret["code"])
                return cls.RUN_ERROR
        elif msg == "NotFound":
            return cls.NOT_FOUND
        elif msg == "Running":
            return cls.RUNNING

    @classmethod
    def pack(cls, id: list[str]):
        cls.check(get(SER+"/path/merge", data=json.dumps(id)))
        cls.check(get(SER+"/pack/start"))
        ret = cls.check(get(SER+"/pack/available"))
        if not isinstance(ret, dict):
            return None
        while ret["msg"] == "Available":
            if ret["msg"] == "Error":
                getLogger("Server").error("Pack Failed.")
                cls.pack(id)
            elif ret["msg"] == "NotFound":
                getLogger("Server").error("Id not found.")
                return None
        return 0

    @classmethod
    def progress(cls):
        done, total = cls.check(get(SER+"/progress/get"))
        assert isinstance(done, int) and isinstance(total, int)
        if total == 0:
            print("Running...                       ", end='\r')
        else:
            print("Running %03d/%03d  %*.01f%%" %
                  (done, total, 5, (done/total)*100), end='\r')

    @classmethod
    def clean(cls):
        cls.check(get(SER+"/progress/reset"))
