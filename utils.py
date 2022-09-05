from requests import get
from requests.utils import quote  # type: ignore
from log import getLogger
from os.path import isfile, isdir
from os import mkdir,remove
from re import match, sub
from alive_progress import alive_bar
# TODO: multiprocessing
from multiprocessing import Process
from subprocess import PIPE, run

from model import Book, ChapterList, Chapter
from tts import tts

from exceptions import ErrorHandler
from exceptions import ServerError, AppError
from requests.exceptions import RequestException


import consts
from typing import Any,TypeVar
from azure.cognitiveservices.speech.speech import ResultFuture


def req(param:tuple[str,list[Any]], caller="Requester", logger=None,
        level=1, exit=False, wait=False):
    getLogger("request").debug("param=%s,caller=%s" % (param, caller))
    try:
        url,args = param
        url = url.format(args[0],*[quote(str(i)) for i in args[1:]])
        getLogger("request").debug("url=%s"%url)
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
        url = consts.GET_SHELF
        shelf: dict = req((url,[self.ip]), 'ToApp', level=2, exit=True, wait=True)  # type: ignore
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

    def get_charpter_list(self, book: Book):
        url = consts.GET_CHAPTER_LIST
        chapters = req((url,[self.ip, book.url]), "ToApp", level=2, exit=True, wait=True)
        if chapters is None:
            return
        return [ChapterList(**item, book=book.url) for item in chapters]

    def download_content(self, chapters: list[ChapterList]):
        retry = []
        con = []
        with alive_bar(len(chapters)) as bar:
            for ch in chapters:
                url = consts.GET_CONTENT
                res = req((url,[self.ip, ch.url, ch.idx]), "ToApp")
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
        con=chap.content
        lines=con.splitlines()
        totLines=len(lines)
        content=[]
        i=0
        while i<totLines:
            tem=""
            getLogger("DEBUG").debug(f"i={i} totLines={totLines}")
            while len(tem)<1500 and i<totLines:
                tem+=lines[i]
                tem+="\n"
                i+=1
            content.append(consts.SSML_MODEL.format(tem))
        return content

    def title(self, chap: Chapter):
        title = sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!]''', "", chap.title)
        title = str(chap.idx)+"_"+chap.title
        return title

    def __call__(self, chap: Chapter):
        if self.type == 1:
            opt:list[Chapter] = []
            title=self.title(chap)
            content=self.content_basic(chap)
            for i,t in enumerate(content):
                opt.append(Chapter(chap.idx,title+f" ({i}).mp3",t,i))
            return opt

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
                            self.logger.debug("audio_duration="+str(ret.audio_duration))
                            if ret.reason != consts.TTS_SUC:
                                self.logger.error(ret.reason)
                                self.logger.error(ret.cancellation_details)
                                self.logger.debug(chapters[j].idx)
                                self.logger.debug("SSML Text: " + chapters[j].content)
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

def _merge(logger,ch,name,is_remove):
    optDir=consts.OPT_DIR
    logger.debug(f"Start merging '{name}'")
    paths=[optDir+"/"+i.title for i in ch]
    cmd=[
        'ffmpeg',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(paths)}',
        '-c',
        'copy',
        '-y',
        optDir+"/"+name.replace(" (0).mp3",".mp3")
    ]
    try:
        ret=run(cmd,stderr=PIPE)
        if ret.returncode != 0:
            logger.error(ret.stderr.decode("utf-8"))
            logger.error("Error occurred while merging. code=%d"%ret.returncode)
        else:
            logger.debug(ret.stderr.decode("utf-8"))
            if is_remove:
                for path in paths:
                    try:
                        remove(path)
                    except Exception as e:
                        ErrorHandler(e,"Remove",logger)()
    except Exception as e:
        ErrorHandler(e, "merge",logger)()

def merge(chapters:list[Chapter],is_remove=True):
    logger = getLogger("Merge")
    ch=[]
    idx=-1
    name=""
    for chap in chapters:
        if chap.idx == idx:
            ch.append(chap)
        else:
            if ch==[]:
                idx=chap.idx
                name=chap.title
                ch=[chap]
                continue
            _merge(logger,ch,name,is_remove)
            idx=chap.idx
            name=chap.title
            ch=[chap]
    _merge(logger,ch,name,is_remove)
