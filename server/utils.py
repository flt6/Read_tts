from requests import get, post
from requests.utils import quote  # type: ignore
from subprocess import PIPE, run
from os.path import isfile, isdir
from shutil import rmtree
from json import dumps
from uuid import uuid1
from html import escape
from os import mkdir, remove, listdir
from re import sub

from model import Chapter
from tts import tts
from log import getLogger

from exceptions import ErrorHandler
from exceptions import ServerError, AppError

from typing import Any
from azure.cognitiveservices.speech.speech import ResultFuture
from azure.cognitiveservices.speech import SpeechSynthesisResult
from log import Log

import consts


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


class Progress:
    def __init__(self, total: int):
        self.id = uuid1().hex
        post("http://127.0.0.1:8080/progress/add",
             data=dumps({"num": total, "uuid": self.id}))

    def close(self):
        post("http://127.0.0.1:8080/progress/end", params={"uuid": self.id})

    def __call__(self) -> None:
        getLogger("progress").debug("Call")
        post("http://127.0.0.1:8080/progress/bar", params={"uuid": self.id})


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
        con_lines = con.splitlines()
        totLines = len(con_lines)
        content = []
        i = 0
        tem = ""
        while i < totLines:
            cut = tem
            tem = ""
            if self.area.empty():
                area = (-1, -1)
            else:
                area = self.area.pop()
            cnt = 0
            while len(cut) < config.MAX_CHAR and i < totLines and cnt+tem.count("\x02") < 24:
                if i >= area[0] and i <= area[1]:
                    tem += con_lines[i] + "\n"
                else:
                    cut += con_lines[i] + "\n"
                if i == area[1] and len(cut) < config.MAX_CHAR and i < totLines and cnt+tem.count("\x02") < 24:
                    cut += tem
                    cnt += tem.count("\x02")
                    tem = ""
                    if self.area.empty():
                        area = (-1, -1)
                    else:
                        area = self.area.pop()
                    
                i += 1
            cut = escape(cut)
            cut = cut.replace("\x01", '</prosody></voice><voice name="zh-CN-YunxiNeural"><prosody rate="18%" pitch="0%">')
            cut = cut.replace("\x02", '</prosody></voice><voice name="zh-CN-XiaohanNeural"><prosody rate="18%" pitch="0%">')
            if cut.count("</voice>") > 50:
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
        for i, line in enumerate(con.splitlines()):
            INVALID = 0xFFFFFFFF
            tem = INVALID
            # This shouldn't be used. As a result, an IndexError will be raised.
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
        tem = i
        cnt += 1
        return tem

    def title(self, chap: Chapter):
        title = sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!]''', "", chap.title)
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
                return Trans(1)(chap)
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
        self.logger.debug("Class 'ToServer' init successfully.")

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
                        logger.error("429: UPS limited error")
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
                    logger.error("Reason: "+ str(ret.reason))
                    logger.debug("idx=%d" % chapters[j].idx)
                    raise RuntimeError("ret.reason=%s" % ret.reason)
                else:
                    assert ret.audio_duration is not None, "Audio here should not be not available. All error should be catched below."
                    self.total_time += ret.audio_duration.total_seconds() / 60
                    if ret.audio_duration.total_seconds() == 0:
                        logger.error("audio_duration=0 and not due to 429")
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
        Progress(len(chapters))
        # description="%02d task for one time" % max_task
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
        bar.close()
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

def _concat(tmp:list[str],name:str, optDir:str):
    paths = [f"{optDir}/{i}" for i in tmp]
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-i",
        f'concat:{"|".join(paths)}',
        "-c",
        "copy",
        "-y",
        optDir + "/" + name,
    ]
    if paths != []:
        print(cmd)
        run(cmd)
        for f in paths:
            remove(f)

def reConcat(optDir):
    files = listdir(optDir)
    name = ""
    tmp: list[str] = []
    for file in files:
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
    hour = time // 3600
    min = time // 60
    sec = time % 60
    return "%02d:%02d:%02d" % (hour, min, sec)


def delete(path):
    if isfile(path):
        remove(path)
    if isdir(path):
        rmtree(path)
