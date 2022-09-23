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

def chk(num:int):
    o=0
    while num:
        o|=num&1
        num>>=1
    return o

class ToApp:
    CHECKIP = 0b0001
    GETIP   = 0b0010
    SAVEIP  = 0b0100
    AUTO    = 0b1000
    def __init__(self,mode=0b1001):
        '''
            @param mode:
                use `|` to set mode based on 0
        '''
        # `mode` dealing is based on binary calculation. 
        self.logger = getLogger("ToApp")
        self.logger.debug(mode)
        if mode != self.AUTO:
            self.logger.warning("ToApp is initialized with `Not run` mode, which means `ip` may not be available.")
        if chk(mode & self.CHECKIP):
            rst = self.checkIP()
            if not rst:
                self.logger.error("Check IP failed.")
                mode |= self.GETIP|self.SAVEIP * chk(mode & self.AUTO)
            else:
                self.logger.info("Check IP Success.")
        if chk(mode & self.GETIP):
            self.logger.debug("Get IP Start.")
            self.getIP()
        if chk(mode & self.SAVEIP):
            self.saveIP(self.ip)

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
        book = books[num]
        return book

    def choose_area(self,book:Book):
        bgn = input(
            "From(%d: %s): " % (
                book.idx,
                book.title
            )
        )
        bgn = book.idx if bgn == '' else int(bgn)
        to = int(input("To. "))
        return range(bgn, to)
    
    def choose_single(self,book):
        chaps=input("chapters(eg: '1 2 3'): ").split(" ")
        return list({int(i) for i in chaps})

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
            res = get(consts.GET_SHELF.format(ip),timeout=3)
            self.logger.debug("HTTP connect status_code=%d" % res.status_code)
            if res.status_code != 200:
                raise ServerError(res.status_code)  # type: ignore
            return True
        except RequestException:
            self.logger.debug("Can't connect to server")
            return False
        except Exception as e:
            ErrorHandler(e, "testIP", self.logger, 2)()

    def checkIP(self):
        if isfile("ip.conf"):
            try:
                with open("ip.conf", "r") as f:
                    ip = f.read()
                    self.logger.debug("Set ip=%s" % ip)
                    if self._testIP(ip):
                        self.ip = ip
                        return True
            except Exception as e:
                ErrorHandler(e, "ToApp", self.logger)()
            self.logger.debug("_testIP() returned False")
        return False
    def getIP(self):
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

    def saveIP(self,ip:str):
        if isdir("ip.conf"):
            print("Directory 'ip.conf' already exists.")
            print("Please delete it first, or IP can't be saved.")
            e = FileExistsError("Directory 'ip.conf' exists.")
            ErrorHandler(e, "ToApp")()
            return
        try:
            with open("ip.conf", "w") as f:
                f.write(ip)
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
    def main_start(cls, type: int) -> Union[str,None]:
        ret = get(SER+"/main/start", params={"type": type})
        ret = cls.check(ret)
        if isinstance(ret, dict):
            getLogger("Server").error(str(ret))
            return None
        assert isinstance(ret, str)
        return ret

    @classmethod
    def main_clean(cls) -> None:
        cls.check(get(SER+"/main/clean"))

    @classmethod
    def init(cls) -> None:
        cls.check(get(SER+"/main/retry/clear"))
    
    @classmethod
    def get_retry(cls) -> list[Chapter]:
        l=cls.check(get(SER+"/main/retry/get"))
        retry=[]
        for chap in l:
            chap["index"] = chap["idx"]  # type: ignore
            retry.append(Chapter(**chap)) # type: ignore
        return retry

    @classmethod
    def get_fail(cls):
        return tuple(cls.check(get(SER+"/main/fail/get")))

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
    def pack(cls, id: list[str],fix=False):
        cls.check(get(SER+"/path/merge", data=json.dumps(id),params={"clean": not(fix)}))
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
    def progress_new(cls):
        done, total = cls.check(get(SER+"/progress/get"))
        assert isinstance(done, int) and isinstance(total, int)
        if cls.bar is None:
            cls.bar = alive_bar()
        if total == 0:
            print("Running...                       ", end='\r')
        else:
            print("Running %03d/%03d  %*.01f%%" %
                  (done, total, 5, (done/total)*100), end='\r')

    @classmethod
    def clean(cls):
        cls.check(get(SER+"/progress/reset"))
