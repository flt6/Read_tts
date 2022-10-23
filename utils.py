from html import escape
from os import listdir, mkdir, remove
from os.path import isdir, isfile
from re import match, search, sub
from subprocess import PIPE, run
from threading import Thread
from time import sleep

from alive_progress import alive_bar
from azure.cognitiveservices.speech import SpeechSynthesisResult
from azure.cognitiveservices.speech.speech import ResultFuture
from requests import get
from requests.exceptions import RequestException
from requests.utils import quote  # type: ignore

import config
import consts
from exceptions import AppError, ErrorHandler, ServerError, UPSLimittedError
from log import Log, getLogger
from model import Book, Chapter, ChapterList
from tts import tts


def req(param, caller="Requester", logger=None,
        level=1, exit=False, wait=False):
    try:
        url, args = param
        url = url.format(args[0], *[quote(str(i)) for i in args[1:]])
        getLogger("request").debug("url=%s,caller=%s" % (url, caller))
        res = get(url, timeout=config.TIMEOUT)
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


def chk(num: int):
    o = 0
    while num:
        o |= num & 1
        num >>= 1
    return o


class ToApp:
    def __init__(self):
        self.logger = getLogger("ToApp")

    def init(self):
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
                self.logger.debug(consts.lang[0])
                continue
            if book.idx == 0:
                self.logger.debug(consts.lang[1])
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

    def choose_area(self, book: Book):
        bgn = input(
            "From(%d: %s): " % (
                book.idx,
                book.title
            )
        )
        bgn = book.idx if bgn == '' else int(bgn)
        to = int(input("To. "))
        return range(bgn, to)

    def choose_single(self):
        chaps = input(consts.lang[2]).strip().split(" ")
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
            self.logger.debug(consts.lang[3])
            return False
        try:
            res = get(consts.GET_SHELF.format(ip), timeout=config.TIMEOUT)
            self.logger.debug(consts.lang[4] % res.status_code)
            if res.status_code != 200:
                raise ServerError(res.status_code)  # type: ignore
            return True
        except RequestException:
            self.logger.debug(consts.lang[5])
            return False
        except Exception as e:
            ErrorHandler(e, "testIP", self.logger, 2)()

    def getIP(self):
        ip = ""
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
            _ip = input("ip: ")
            ip = _ip if _ip != "" else ip
            if ":" not in ip:
                ip += ":1122"
            self.logger.debug("Set ip=%s" % ip)
            if self._testIP(ip):
                self.ip = ip
                return
            else:
                self.logger.debug("_testIP() returned False")
                print(consts.lang[6])

    def saveIP(self):
        if isdir("ip.conf"):
            print(consts.lang[7])
            print(consts.lang[8])
            e = FileExistsError(consts.lang[9])
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
        con = chap.content
        con = chap.title+"\n"+con
        lines = con.splitlines()
        totLines = len(lines)
        content = []
        i = 0
        while i < totLines:
            tem = ""
            while len(tem) < config.MAX_CHAR and i < totLines:
                tem += lines[i]
                tem += "\n"
                i += 1
            tem = escape(tem)
            content.append(consts.SSML_MODEL.format(tem))
        return content

    def title(self, chap: Chapter):
        title = sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!]''', "", chap.title)
        title = "%03d" % chap.idx+"_"+title
        return title

    def __call__(self, chap: Chapter):
        if self.type == 1:
            opt: list[Chapter] = []
            title = self.title(chap)
            content = self.content_basic(chap)
            for i, t in enumerate(content):
                opt.append(Chapter(chap.idx, title+f" ({i}).mp3", t))
            return opt


class ToServer:
    def __init__(self, optDir):
        self.logger = getLogger("ToServer")
        self.optDir = optDir
        self.total_time = 0
        self.createdir()
        self.logger.debug(consts.lang[10])

    def createdir(self):
        if not isdir(self.optDir):
            mkdir(self.optDir)

    def _callback(self, task: ResultFuture, j, retry, chapters, bar):
        ret = task.get()
        self._deal(ret, j, retry, chapters, bar)

    def callback(self, task, j, retry: set[Chapter], chapters, bar):
        thr = Thread(target=self._callback, args=(
            task, j, retry, chapters, bar))
        thr.start()
        return thr

    def _deal(self, ret: SpeechSynthesisResult, j, retry: set[Chapter], chapters, bar):
        logger = getLogger("callback")
        try:
            logger.debug(
                "audio_duration="+str(ret.audio_duration))
            self.total_time += ret.audio_duration.total_seconds()/60
            if ret.reason == consts.TTS_CANCEL:
                detail = ret.cancellation_details
                logger.debug("Canceled")
                logger.debug("idx=%d"%chapters[j].idx)
                logger.debug("Detail: "+str(detail))
                logger.debug("code: "+str(detail.error_code))
                if detail.error_code==429:
                    logger.error(consts.lang[11])
                    raise UPSLimittedError(detail.error_details)
            if ret.reason != consts.TTS_SUC:
                logger.debug("Error")
                logger.error(consts.lang[12]+str(ret.reason))
                logger.debug("idx=%d"%chapters[j].idx)
                logger.debug(
                    "SSML Text: " + chapters[j].content)
                raise RuntimeError("ret.reason=%s" % ret.reason)
            if ret.audio_duration.total_seconds() == 0:
                logger.error(consts.lang[13])
                raise RuntimeError("audio_duration=0")
        except BaseException as e:
            ErrorHandler(e, "AsyncReq", logger)()
            retry.add(chapters[j])
        retry_len = len(retry)
        total = 1 if bar.current() == 0 else bar.current()+1
        persent = 1-(retry_len/total)
        bar.text = consts.lang[14] % (
            retry_len, persent*100)
        bar()

    def asyncDownload(self, chapters: list[Chapter], max_task: int = config.MAX_TASK):
        pool: list[Thread] = []
        retry: set[Chapter] = set()
        self.retry_len = 0
        self.total_len = 0
        stop_cnt=0
        with alive_bar(len(chapters),bar="circles",dual_line=True) as bar:
            bar.title = "%02d task for one time" % max_task
            for i, chap in enumerate(chapters):
                opt = self.optDir+'/'+chap.title
                task = tts(chap.content, opt)
                self.logger.debug(f"Create task {task}")
                pool.append(self.callback(task, i, retry, chapters, bar))
                if len(pool) < max_task: continue
                self.logger.info("Start waiting.")
                while len(pool) >= max_task:
                    sleep(2)
                    tmp = []
                    for thr in pool:
                        if thr.is_alive():
                            tmp.append(thr)
                    pool = tmp.copy()
                    # This should be like `ptr.png`

                    total = bar.current()+1
                    persent = -1
                    if total-self.total_len == 0:
                        persent = 1
                    else:
                        persent = 1-((len(retry)-self.retry_len)/(total-self.total_len))
                        if total-self.total_len<config.FAIL_429:
                            persent = 1
                        self.logger.debug("total=%02d       total_len=%02d"%(total,self.total_len))
                        self.logger.debug("len(retry)=%02d  retry_len=%02d"%(len(retry),self.retry_len))
                        self.retry_len, self.total_len = len(retry), total
                    self.logger.debug("persent= %f"%persent)
                    if persent < config.LIMIT_429:
                        stop_cnt+=1
                        self.logger.error("429 UPS Limitted.")
                        self.logger.info("Waiting for all runnning jobs...")
                        for thr in pool:
                            thr.join()
                        t = 9+3*stop_cnt
                        if t>config.MAX_WAIT:
                            t=15
                        self.logger.info("Sleep for %02d seconds..."%t)
                        sleep(t)
                        self.logger.info("UPS error wait end")
                self.logger.info("End waiting.")
            # ----------------------------------------------
            self.logger.info("Start last async waiting.")
            for thr in pool:
                thr.join()
            self.logger.info("End async waiting.")
            # ----------------------------------------------
        return retry


def _merge(dir: str, logger: Log, ch: list[Chapter], name: str, is_remove: bool):
    logger.debug(f"Start merging '{name}'")
    paths = [dir+"/"+i.title for i in ch]
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(paths)}',
        '-c',
        'copy',
        '-y',
        dir+"/"+name.replace(" (0).mp3", ".mp3")
    ]
    try:
        ret = run(cmd, stderr=PIPE)
        if ret.returncode != 0:
            logger.error(ret.stderr.decode("utf-8"))
            logger.error("Error occurred while merging. code=%d" %
                         ret.returncode)
        else:
            logger.debug(ret.stderr.decode("utf-8"))
            if is_remove:
                for path in paths:
                    try:
                        remove(path)
                    except Exception as e:
                        ErrorHandler(e, "Remove", logger)()
    except Exception as e:
        ErrorHandler(e, "merge", logger)()


def _concat(tmp: list[str], name: str):
    paths = [config.OPT_DIR+"/"+i for i in tmp]
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(paths)}',
        '-c',
        'copy',
        '-y',
        config.OPT_DIR+"/"+name
    ]
    if paths != []:
        print(cmd)
        run(cmd)
        for f in paths:
            remove(f)


def reConcat():
    l = listdir(config.OPT_DIR)
    name = ""
    tmp: list[str] = []
    for file in l:
        if " (0).mp3" in file:
            _concat(tmp, name)
            tmp = []
            name = file.replace(" (0).mp3", ".mp3")
        tmp.append(file)
    _concat(tmp, name)


def merge(chapters: list[Chapter], dir: str, is_remove=True):
    logger = getLogger("Merge")
    ch = []
    idx = -1
    name = ""
    for chap in chapters:
        if chap.idx == idx:
            ch.append(chap)
        else:
            if ch == []:
                idx = chap.idx
                name = chap.title
                ch = [chap]
                continue
            _merge(dir, logger, ch, name, is_remove)
            idx = chap.idx
            name = chap.title
            ch = [chap]
    _merge(dir, logger, ch, name, is_remove)


def time_fmt(time: float):
    time = int(time)
    hour = time//3600
    min = time//60
    sec = time % 60
    return "%02d:%02d:%02d" % (hour, min, sec)


def redelete():
    try:
        l = listdir(config.OPT_DIR)
        for i in l:
            if search(r"\s\(\d+\)\.mp3$", i) is not None:
                path = config.OPT_DIR+"/"+i
                if isfile(path):
                    remove(path)
    except Exception as e:
        ErrorHandler(e, "Redelete")
