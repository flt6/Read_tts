from requests import get
from log import getLogger
from os.path import isfile, isdir
from os import mkdir
from re import match, sub
from alive_progress import alive_bar
# TODO: multiprocessing
from multiprocessing import Process

from model import Book, ChapterList, Chapter
from tts import tts

from exceptions import ErrorHandler
from exceptions import ServerError, AppError
from requests.exceptions import RequestException


import consts
from typing import Union
from azure.cognitiveservices.speech.speech import ResultFuture


def req(url, caller="Requester", logger=None,
        level=1, exit=False, wait=False):
    getLogger("request").debug("url=%s,caller=%s" % (url, caller))
    try:
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


class Stack:
    def __init__(self):
        self._st = []

    def push(self, x):
        self._st.append(x)

    def top(self):
        return self._st[-1]

    def pop(self):
        return self._st.pop()

    def length(self):
        return len(self._st)

    def empty(self):
        return self.length() == 0


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
        url = consts.GET_SHELF.format(self.ip)
        shelf: dict = req(url, 'ToApp', level=2, exit=True, wait=True)
        books = []
        for i in range(len(shelf)):
            book = Book(**shelf[i])
            if not book.available:
                self.logger.debug("Book not available")
                continue
            if book.idx == 0:
                self.logger.debug(f"No ChaperIndex.")
                continue
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

    def get_charpter_list(self, book: Book) -> list[ChapterList]:
        url = consts.GET_CHAPTER_LIST.format(self.ip, book.url)
        chapters = req(url, "ToApp", level=2, exit=True, wait=True)
        return [ChapterList(**item, book=book.url) for item in chapters]

    def download_content(self, chapters: list[ChapterList]):
        retry = []
        con = []
        with alive_bar(len(chapters)) as bar:
            for ch in chapters:
                url = consts.GET_CONTENT.format(self.ip, ch.url, ch.idx)
                res = req(url, "ToApp")
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


class Trans:
    def __init__(self, type: int = 1):
        self.type = type

    def content_basic(self, chap: Chapter):
        chap.content = consts.SSML_MODEL.format(chap.content)
        return chap

    def title(self, chap: Chapter):
        chap.title = sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!]''', "", chap.title)
        chap.title = str(chap.idx)+"_"+chap.title
        return chap

    def __call__(self, chap: Chapter):
        if self.type == 1:
            return self.title(self.content_basic(chap))


class ToServer:
    def __init__(self, optDir):
        self.logger = getLogger("ToServer")
        self.optDir = optDir
        self.createdir()
        self.logger.debug("Class 'ToServer' init successfully.")

    def createdir(self):
        if not isdir(self.optDir):
            mkdir(self.optDir)

    def asyncDownload(self, chapters: list[Chapter]):
        st: list[tuple[ResultFuture, int]] = []
        retry: list[Chapter] = []
        with alive_bar(len(chapters)) as bar:
            for i, chap in enumerate(chapters):
                opt = self.optDir+'/'+chap.title
                task = tts(chap.content, opt)
                self.logger.debug(f"Create task {task}")
                st.append((task, i))  # type: ignore
                if len(st) >= 5:
                    self.logger.info("Start async waiting.")
                    for task, j in st:
                        try:
                            ret = task.get()
                            if ret.reason != consts.TTS_SUC:
                                self.logger.error(ret.reason)
                                retry.append(chapters[j])
                        except Exception as e:
                            ErrorHandler(e, "AsyncReq", self.logger)
                            retry.append(chapters[j])
                        bar()
                    st = []
                    self.logger.info("End async waiting.")
            self.logger.info("Start last async waiting.")
            if len(st) >= 5:
                self.logger.info("Start async waiting.")
                for task, j in st:
                    try:
                        ret = task.get()
                        if ret.reason != consts.TTS_SUC:
                            self.logger.error(ret.reason)
                            retry.append(chapters[j])
                    except Exception as e:
                        ErrorHandler(e, "AsyncReq", self.logger)
                        retry.append(chapters[j])
                    bar()
                self.logger.info("End async waiting.")
        return retry


def test_app():
    print("Before this test, you should set ip in `ip.conf`")
    app = ToApp()
    bk = app.get_shelf()[0]
    l = app.get_charpter_list(bk)[0:5]
    con = app.download_content(l)[0]
    print(con)

def test_trans():
    con = [
        Chapter(0, "Test title 0", 'Content text 0'),
        Chapter(1, "Test title 1", 'Content text 1')
    ]
    rst=[
        '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">\n    <voice name="zh-CN-XiaoxiaoNeural">\n        <prosody rate="43%" pitch="0%">\n            Content text 0\n        </prosody>\n    </voice>\n</speak>',
        '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">\n    <voice name="zh-CN-XiaoxiaoNeural">\n        <prosody rate="43%" pitch="0%">\n            Content text 1\n        </prosody>\n    </voice>\n</speak>'
    ]
    t = Trans()
    for i in con:
        i = t(i)
    for i in range(len(con)):
        assert con[i].content == rst[i]

def test_tts():
    con = [
        Chapter(0, "Test title 0", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 0</prosody></voice></speak>'),
        Chapter(1, "Test title 1", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 1</prosody></voice></speak>')
    ]
    ser = ToServer("Output")
    ser.asyncDownload(con)


if __name__ == '__main__':
    test_trans()
