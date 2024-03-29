import asyncio
from pickle import dumps, loads
from html import escape
from os import listdir, mkdir, remove
from os.path import isdir, isfile
from re import match, search, sub
from subprocess import PIPE, run
from time import sleep

from mytts import CancellationErrorCode, SpeechSynthesisResult
import requests
from requests.exceptions import RequestException
from requests.utils import quote  # type: ignore
from typing import Optional
from rich import print
from rich.columns import Columns
from rich.panel import Panel
from rich.progress import Progress, TaskID
from rich.traceback import Traceback
from traceback import format_exception

import config
import consts
from exceptions import AppError, ErrorHandler, ServerError, UPSLimittedError
from log import Log, getLogger
from model import Book, Chapter, ChapterList
from tts import tts


if isfile("data.dmp") and config.SAVE_REQ:
    with open("data.dmp","rb") as f:
        req_data = loads(f.read())
else:
    req_data = {}

def get(*args,**kwargs) -> requests.Response:
    if not config.SAVE_REQ:
        return requests.get(*args,**kwargs)
    log = getLogger("get")
    dmp = dumps([args, kwargs])
    if dmp not in req_data.keys():
        log.debug("not in req_data")
        ret = requests.get(*args,**kwargs)
        req_data.update({dmp:ret})
        with open("data.dmp","wb") as f:
            f.write(dumps(req_data))
        return ret
    else:
        log.debug("in req_data")
        log.debug(req_data[dmp])
        return req_data[dmp]

def req(param, caller="Requester", logger=None, level=1, exit=False, wait=False):
    try:
        url, args = param
        url = url.format(args[0], *[quote(str(i)) for i in args[1:]])
        getLogger("request").debug("url=%s,caller=%s" % (url, caller))
        res = get(url, timeout=config.TIMEOUT)
        if res.status_code != 200:
            raise ServerError(res.status_code) # type: ignore
    except Exception as e:
        ErrorHandler(e, caller, logger, level, exit, wait)()
        return None
    try:
        json = res.json()
        if not json["isSuccess"]:
            raise AppError(json["errorMsg"])  # type: ignore
        json = json["data"]
    except Exception as e:
        ErrorHandler(e, caller, logger, level, exit, wait)()
        return None
    return json


class Stack:
    def __init__(self):
        self._arr = []
        self._typ = None

    def push(self, t) -> None:
        if self._typ is None:
            self._typ = type(t)
        elif type(t) != self._typ:
            raise TypeError(
                f"The new object should be '{self._typ}', but '{type(t)}'")
        self._arr.append(t)

    def pop(self):
        t = self._arr.pop()
        assert type(t) == self._typ, "The popped object is not the same with the others. May caused by editting inner variables directly."
        return t

    def empty(self):
        return not self._arr

    def clear(self):
        self._arr.clear()
        self._typ = None

    def __rich_repr__(self):
        yield "Stack"
        yield f"length: {len(self._arr)}"
        contain = ", ".join(map(str, self._arr))
        yield f"contain: {contain}"


class Queue:
    '''
    self._arr is a set.
    '''

    def __init__(self):
        self._arr = list()
        self._typ = None

    def push(self, t) -> None:
        if self._typ is None:
            self._typ = type(t)
        elif type(t) != self._typ:
            raise TypeError(
                f"The new object should be '{self._typ}', but '{type(t)}'")
        if t not in self._arr:
            self._arr.append(t)

    def pop(self):
        t = self._arr.pop(0)
        assert type(t) == self._typ, "The popped object is not the same with the others. May caused by editting inner variables directly."
        return t

    def empty(self):
        return len(self._arr) == 0

    def clear(self):
        self._arr.clear()
        self._typ = None

    def __repr__(self) -> str:
        contain = ""
        for obj in self._arr:
            contain += str(obj)
            contain += ", "
        return f"<Stack len={len(self._arr)} contain={contain}>"

    def __str__(self) -> str:
        return self.__repr__()

    def __rich_repr__(self):
        yield "Stack"
        yield f"length: {len(self._arr)}"
        contain = ""
        for obj in self._arr:
            contain += str(obj)
            contain += ", "
        yield f"contain: {contain}"


class ToApp:
    def __init__(self):
        self.logger = getLogger("ToApp")

    def init(self):
        self.getIP()
        config.update({"ip": self.ip})

    def get_shelf(self):
        """
        Get the shelf infomation from the app.
        @return: Is succeeded.
        """
        shelf: dict = req(
            (consts.GET_SHELF, [self.ip]), "ToApp", level=2, exit=True, wait=True
        )  # type: ignore
        books = []
        t = []
        for i, shelf_item in enumerate(shelf):
            book = Book(**shelf_item)
            if not book.available:
                self.logger.debug(config.lang["utils"]["ToApp"]["not_avai"])
                continue
            if book.idx == 0:
                self.logger.debug(config.lang["utils"]["ToApp"]["no_chap"])
            tip = consts.CHOOSEBOOK % (i + 1, book.name, book.author, book.idx)
            t.append(Panel(tip, expand=True))
            books.append(book)
        print(Columns(t, equal=True))
        return books

    def choose_book(self, books: list[Book]):
        num = int(input("No. ")) - 1
        book = books[num]
        return book

    def choose_area(self, book: Book):
        bgn = input("From(%d: %s): " % (book.idx, book.title))
        bgn = book.idx if bgn == "" else int(bgn)
        to = int(input("To. "))
        return range(bgn, to)

    def choose_single(self):
        chaps = input(config.lang["utils"]["ToApp"]
                      ["retry_pro"]).strip().split(" ")
        return list({int(i) for i in chaps})

    def get_charpter_list(self, book: Book):
        chapters = req(
            (consts.GET_CHAPTER_LIST, [self.ip, book.url]), "ToApp", level=2, exit=True, wait=True
        )
        if chapters is None:
            return
        return [ChapterList(**item, book=book.url) for item in chapters]

    def download_content(self, chapters: list[ChapterList]):
        retry = []
        con = []
        with Progress() as pro:
            task = pro.add_task("Download chapters", total=len(chapters))
            for ch in chapters:
                try:
                    pro.update(task, advance=1)
                    res = req((consts.GET_CONTENT, [self.ip, ch.url, ch.idx]), "ToApp")
                except ServerError as e: # type: ignore
                    if e.msg == "404": # type: ignore
                        retry.append(ch)
                        continue
                if res is None:
                    retry.append(ch)
                    continue
                con.append(Chapter(ch.idx, ch.title, res))
        return (con, retry)

    def _testIP(self, ip: str):
        ret = match(r"(\d{1,3}\.){3}\d{1,3}(:\d{1,5})?", ip)
        if not ret or ret.group()!=ip:
            self.logger.debug(config.lang["utils"]["ToApp"]["re_fail"])
            return False
        try:
            res = get(consts.GET_SHELF.format(ip), timeout=config.TIMEOUT)
            self.logger.debug(
                config.lang["utils"]["ToApp"]["http_dbg"] % res.status_code
            )
            if res.status_code != 200:
                raise ServerError(res.status_code)  # type: ignore
            return True
        except RequestException:
            self.logger.debug(config.lang["utils"]["ToApp"]["ser_fail"])
            return False
        except Exception as e:
            ErrorHandler(e, "testIP", self.logger, 2)()

    def getIP(self):
        ip = config.ip
        if self._testIP(ip):
            self.ip = ip
            return
        while True:
            _ip = input("ip: ")
            ip = _ip if _ip else ip
            if ":" not in ip:
                ip += ":1122"
            self.logger.debug("Set ip=%s" % ip)
            if self._testIP(ip):
                self.ip = ip
                return
            else:
                self.logger.debug("_testIP() returned False")
                print(config.lang["utils"]["ToApp"]["app_fail"])


class Trans:
    def __init__(self, type: Optional[int] = 1):
        self.type = type
        self.area = Queue()
        self.open_bracket = config.bracket[0]
        self.close_bracket = config.bracket[1]
        self.logger = getLogger("Trans")

    def trans(self, chap: Chapter):
        con = chap.content
        con = chap.title + "\n" + con
        con_lines = con.splitlines() # source content lines
        totLines = len(con_lines)
        content = [] # formatted content, list[str(SSML)]
        i = 0
        tem = "" # temporary content, for the some lines left by last turn
        while i < totLines:
            cut = tem
            tem = ""
            if self.area.empty():
                area = (-1, -1)
            else:
                area = self.area.pop()
            bracket_num = cut.count("\x02")
            # len(cut) < config.MAX_CHAR         : Make sure the total character is less than the order.
            # i < totLines                       : Loop all the lines.
            # bracket_num+tem.count("\x02") < 24 : Make sure the <voice> tag is less than 50(half=25, basic 1).
            while len(cut) < config.MAX_CHAR and i < totLines and bracket_num+tem.count("\x02") < 24:
                if i >= area[0] and i <= area[1]:
                    tem += con_lines[i] + "\n"
                else:
                    cut += con_lines[i] + "\n"
                if i == area[1] and len(cut) < config.MAX_CHAR and i < totLines and bracket_num+tem.count("\x02") < 24:
                    cut += tem
                    bracket_num += tem.count("\x02")
                    tem = ""
                    if self.area.empty():
                        area = (-1, -1)
                    else:
                        area = self.area.pop()
                    
                i += 1
            cut = escape(cut)
            cut = cut.replace("\x01", '</prosody></voice><voice name="zh-CN-YunxiNeural"><prosody rate="18%" pitch="0%">')
            cut = cut.replace("\x02", '</prosody></voice><voice name="zh-CN-XiaohanNeural"><prosody rate="18%" pitch="0%">')
            if cut.count("</voice>") > 49:
                self.logger.error("Voice tag out of limit.")
                self.logger.debug(con)
                raise AssertionError("Voice tag out of limit.")
            content.append(consts.SSML_MODEL.format(cut))
        return content

    def _chk(self, con: str):
        st = Stack()
        self.area.clear()
        cnt = 0
        newst: list[str] = []
        log = []
        INVALID = 0xFFFFFFFF
        tem = INVALID
        # This shouldn't be used. As a result, an IndexError will be raised.
        for i, line in enumerate(con.splitlines()):
            tmp_line = [s for s in line]
            for j, ch in enumerate(line):
                if ch in self.open_bracket and tem == INVALID:
                    tem = self._chk_push(st, cnt, log, i, line, tmp_line, j, ch)
                elif ch in self.close_bracket and tem != INVALID:
                    self.area.push((tem+1, i+1))
                    log.append(f'line {i}: {line}')
                    log.append(f'character {j}: pop')
                    tmp_line[j] = "\x02"
                    tem = INVALID
                    top = st.pop()
                    if top != self.close_bracket.index(ch):
                        self.logger.debug("Scan failed.")
                        self.logger.debug(tmp_line)
                        return None
            tmp_line = ''.join(tmp_line)
            newst.append(tmp_line)
        if self.area.empty():
            self.area.push((-1, -1))
        if not st.empty():
            self.logger.debug("Scan failed.")
            self.logger.debug(f"Not empty: {st._arr}")
            self.logger.debug(log)
            return None
        return newst

    def _chk_push(self, st, cnt, log, i, line, tmp_line, j, ch):
        st.push(self.open_bracket.index(ch))
        log.append(f'line {i}: {line}')
        log.append(f'character {j}: push')
        tmp_line[j] = "\x01"
        cnt += 1
        return i

    def title(self, chap: Chapter):
        title = sub(r"""[\*\/\\\|\<\>\? \:\.\'\"\!]""", "", chap.title)
        title = f"{chap.idx:03d}_{title}"
        return title

    def __call__(self, chap: Chapter):
        title = self.title(chap)
        opt: list[Chapter] = []
        if self.type == 1:
            content = self.trans(chap)
            for i, t in enumerate(content):
                opt.append(Chapter(chap.idx, f"{title} ({i}).mp3", t))
            return opt
        elif self.type == 2:
            self.logger.debug(
                f"Start handling {chap.title} with character mode.")
            chsp_src = chap.copy()
            try:
                con_lines = self._chk(chap.content)
                assert con_lines is not None
                chap.content = "\n".join(con_lines)
                content = self.trans(chap)
            except AssertionError as e:
                self.logger.error(
                    "Character transfering scan failed, falling back to basic.")
                self.logger.debug(chap.title)
                ErrorHandler(e, "Trans", self.logger)
                return Trans(1)(chsp_src)
            for i, t in enumerate(content):
                opt.append(Chapter(chap.idx, f"{title} ({i}).mp3", t))
            return opt


class ToServer:
    def __init__(self, optDir):
        self.logger = getLogger("ToServer")
        self.optDir = optDir
        self.finished: list[tuple[SpeechSynthesisResult, int]] = []
        self.ups = False
        self.total_time = 0
        self.createdir()
        self.logger.debug(config.lang["utils"]["ToSer"]["init"])

    def createdir(self):
        if not isdir(self.optDir):
            mkdir(self.optDir)

    def _callback(self, task: asyncio.Task):
        # To make sure safety of thread, it'll only save finished tasks in an array.
        # Some functions is not recommanded to use due to they are inside functions in `mytts`
        # I use these because `get` method called in thread has some bugs when build this.
        exc = task.exception()
        if exc is None:
            ret = task.result()
        else:
            ret = None
        result = SpeechSynthesisResult(ret, exc)
        id = int(task.get_name())
        self.finished.append((result, id))

    def _deal(self, chapters:list[Chapter], retry:set[Chapter], pro:Progress, pro_task:TaskID, task_cnt:int):
        logger = getLogger("callback")
        for ret, j in self.finished:
            # deal begin
            try:
                logger.debug("audio_duration=" + str(ret.audio_duration))
                if ret.reason == consts.TTS_CANCEL:
                    assert ret.cancellation_details is not None
                    detail = ret.cancellation_details
                    logger.debug("Canceled")
                    logger.debug("idx=%d" % chapters[j].idx)
                    logger.debug("Detail: " + str(detail))
                    logger.debug("code: " + str(detail.error_code))
                    if detail.error_code == CancellationErrorCode.TooManyRequests:
                        self.ups = True
                        logger.error(config.lang["utils"]["ToSer"]["429"])
                        raise UPSLimittedError(detail.error_details)
                    elif detail.error_code == CancellationErrorCode.RuntimeError:
                        logger.error("RuntimeError: ")
                        exc = detail.exception
                        if isinstance(exc, BaseException):
                            print(Traceback.from_exception(
                                type(exc), exc, exc.__traceback__))
                            logger.error("".join(format_exception(
                                type(exc), exc, exc.__traceback__)))
                        else:
                            print(exc)
                            logger.error(exc)
                if ret.reason != consts.TTS_SUC:
                    logger.debug("Error")
                    logger.error(config.lang["utils"]
                                ["ToSer"]["fail"] + str(ret.reason))
                    logger.debug("idx=%d" % chapters[j].idx)
                    raise RuntimeError("ret.reason=%s" % ret.reason)
                else:
                    assert ret.audio_duration is not None, "Audio here should not be not available. All error should be catched below."
                    self.total_time += ret.audio_duration.total_seconds() / 60
                    if ret.audio_duration.total_seconds() == 0:
                        logger.error(config.lang["utils"]["ToSer"]["fail_not_429"])
                        raise RuntimeError("audio_duration=0")
            except BaseException as e:
                ErrorHandler(e, "AsyncReq", logger)()
                retry.add(chapters[j])
            # deal end
            pro.update(pro_task, advance=1)
            task_cnt -= 1
        self.finished.clear()
        return task_cnt
        
    def asyncDownload(self, chapters: list[Chapter], max_task: int = config.MAX_TASK):
        retry: set[Chapter] = set()
        self.retry_len = 0
        self.total_len = 0
        stop_cnt = 0
        with Progress() as pro:
            pro_task = pro.add_task("TTS", total=len(chapters))
            pro.update(
                pro_task, description="%02d task for one time" % max_task)
            task_cnt = 0
            for i, chap in enumerate(chapters):
                opt = self.optDir + "/" + chap.title
                task = tts(chap.content, opt)
                task.set_name(i)
                task.add_done_callback(self._callback)
                self.logger.debug(f"Create task {task}")
                task_cnt += 1
                # self.logger.info("Start waiting.")
                while task_cnt >= max_task:
                    sleep(1)
                    task_cnt = self._deal(chapters, retry, pro, pro_task, task_cnt)
                    if self.ups:
                        self.logger.error("429 UPS Limitted.")
                        self.logger.info("Waiting for all runnning jobs...")
                        while task_cnt > 0:
                            sleep(1)
                            task_cnt = self._deal(chapters, retry, pro, pro_task, task_cnt)
                        self.ups = False
                        stop_cnt += 1
                        t = 9 + 3 * stop_cnt
                        if t > config.MAX_WAIT:
                            t = 15
                        self.logger.info("Sleep for %02d seconds..." % t)
                        sleep(t)
                        self.logger.info("UPS error wait end")
                # self.logger.info("End waiting.")
            # ----------------------------------------------
            print("[yellow1]Start last async waiting.[/yellow1]")
            while task_cnt > 0:
                sleep(1)
                task_cnt = self._deal(chapters, retry, pro, pro_task, task_cnt)
            print("[yellow1]End async waiting.[/yellow1]")
            # ----------------------------------------------
        return retry


def _merge(dir: str, logger: Log, ch: list[Chapter], name: str, is_remove: bool):
    logger.debug(f"Start merging '{name}'")
    paths = [dir + "/" + i.title for i in ch]
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        f'concat:{"|".join(paths)}',
        "-c",
        "copy",
        "-y",
        dir + "/" + name.replace(" (0).mp3", ".mp3"),
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
    paths = [config.OPT_DIR + "/" + i for i in tmp]
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        f'concat:{"|".join(paths)}',
        "-c",
        "copy",
        "-y",
        config.OPT_DIR + "/" + name,
    ]
    if paths != []:
        print(cmd)
        run(cmd)
        for f in paths:
            remove(f)


def reConcat():
    files = listdir(config.OPT_DIR)
    files.sort()
    name = "NEVERAPPEAR"
    tmp: list[str] = []
    for file in files:
        if " (0).mp3" in file:
            xor=lambda a,b:(a and b) or (not a and not b)
            assert xor(name=="NEVERAPPEAR",len(tmp)==0), f"name={name}, tmp={tmp}"
            _concat(tmp, name)
            tmp = []
            name = file.replace(" (0).mp3", ".mp3")
        if search(r"\s\(\d+\)\.mp3$", file) is not None:
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
    hour = time // 3600
    min = time // 60
    sec = time % 60
    return "%02d:%02d:%02d" % (hour, min, sec)


def redelete():
    try:
        l = listdir(config.OPT_DIR)
        for i in l:
            if search(r"\s\(\d+\)\.mp3$", i) is not None:
                path = config.OPT_DIR + "/" + i
                if isfile(path):
                    remove(path)
    except Exception as e:
        ErrorHandler(e, "Redelete")
