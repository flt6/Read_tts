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


def req(param: tuple[str, list[Any]], caller="Requester", logger=None,
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
    def __init__(self, type: int = 1):
        self.type = type

    def content_basic(self, chap: Chapter):
        con = chap.content
        lines = con.splitlines()
        totLines = len(lines)
        content = []
        i = 0
        while i < totLines:
            tem = ""
            getLogger("DEBUG").debug(f"i={i} totLines={totLines}")
            while len(tem) < consts.MAX_CHAR and i < totLines:
                tem += lines[i]
                tem += "\n"
                i += 1
            tem = escape(tem)
            content.append(consts.SSML_MODEL.format(tem))
        return content

    def title(self, chap: Chapter):
        title = sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!\s]''', "", chap.title)
        title = "%03d"%chap.idx+"_"+title
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
        self.createdir()
        self.logger.debug("Class 'ToServer' init successfully.")

    def createdir(self):
        if not isdir(self.optDir):
            mkdir(self.optDir)

    def _download(self, st, retry:set[Chapter], chapters, bar):
        for task, j in st:
            try:
                ret = task.get()
                ret: SpeechSynthesisResult
                self.logger.debug(
                    "audio_duration="+str(ret.audio_duration))
                if ret.audio_duration.total_seconds() == 0:
                    self.logger.error("audio_duration=0")
                    retry.add(chapters[j])
                    raise RuntimeError("Audio duration is zero.")
                if ret.reason != consts.TTS_SUC:
                    self.logger.debug("AsyncReq not success `get`")
                    self.logger.error(ret.reason)
                    self.logger.error(ret.cancellation_details)
                    self.logger.debug(chapters[j].idx)
                    self.logger.debug(
                        "SSML Text: " + chapters[j].content)
                    retry.add(chapters[j])
                    e = RuntimeError("ret.reason=%s" % ret.reason)
                    self.logger.debug("Call ErrorHandler")
                    ErrorHandler(e, "AsyncReq", self.logger)()
            except BaseException as e:
                self.logger.debug("AsyncReq raise at `try`")
                ErrorHandler(e, "AsyncReq", self.logger)()
                retry.add(chapters[j])
            getLogger('bar').debug("bar")
            bar()

    def asyncDownload(self, chapters: list[Chapter]):
        st: list[tuple[ResultFuture, int]] = []
        retry: set[Chapter] = set()
        bar = Progress(len(chapters))
        getLogger("Progress").debug("Call1")
        for i, chap in enumerate(chapters):
            opt = self.optDir+'/'+chap.title
            task = tts(chap.content, opt)
            self.logger.debug(f"Create task {task}")
            st.append((task, i))  # type: ignore
            if len(st) >= consts.MAX_TASK:
                self.logger.info("Start async waiting.")
                self._download(st, retry, chapters, bar)
                st = []
                self.logger.info("End async waiting.")
        # ----------------------------------------------
        self.logger.info("Start last async waiting.")
        self._download(st, retry, chapters, bar)
        self.logger.info("End async waiting.")
        # ----------------------------------------------
        bar.close()
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

def _concat(tmp:list[str],name:str):
    paths = ["Output/"+i for i in tmp]
    cmd = [
        'ffmpeg',
        '-hide_banner',
        '-i',
        f'concat:{"|".join(paths)}',
        '-c',
        'copy',
        '-y',
        "Output/"+name
    ]
    if paths != []:
        print(cmd)
        run(cmd)
        for f in paths:
            remove(f)

def reConcat():
    l = listdir("Output")
    name = ""
    tmp:list[str] = []
    for file in l:
        if " (0).mp3" in file:
            _concat(tmp,name)
            tmp = []
            name = file.replace(" (0).mp3", ".mp3")
        tmp.append(file)
    _concat(tmp,name)

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


def delete(path):
    if isfile(path):
        remove(path)
    if isdir(path):
        rmtree(path)
