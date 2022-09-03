from log import getLogger
from utils import ToApp, ToServer, Trans, merge
from model import Chapter
from os import remove,mkdir,rmdir
from os.path import isfile,isdir
from shutil import copytree,rmtree
from tts import tts
from exceptions import ErrorHandler
import consts
import pytest


def test_log():
    log = getLogger("Test")
    log.debug("Test")
    log.info("Test")
    log.error("Test")
    log.critical("Test")
    try:
        1/0
    except Exception as e:
        log.super._log(40, "Test Source", (), exc_info=True)
        log.exception("Test Exception")

@pytest.fixture()
def cleanup():
    yield None
    remove("logs/debug.log")
    remove("logs/info.log")
    remove("logs/error.log")


def test_TTS():
    t = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 0</prosody></voice></speak>'
    ret = tts(t, "output.mp3").get()  # type: ignore
    remove("output.mp3")
    assert ret.reason == consts.TTS_SUC

class TestUtils:
    def test_app(self):
        print("Before this test, you should set ip in `ip.conf`")
        if not isfile("ip.conf"):
            print("You should set ip in `ip.conf`.")
            return
        app = ToApp()
        bk = app.get_shelf()[0]
        l = app.get_charpter_list(bk)[0:5]
        con = app.download_content(l)[0]
        print(con)


    def test_trans(self):
        con = [
            Chapter(0, "Test title 0", 'Content text 0'),
            Chapter(1, "Test title 1", 'LongText\n'*625)
        ]
        rst = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">\n    <voice name="zh-CN-XiaoxiaoNeural">\n        <prosody rate="43%" pitch="0%">\n            Content text 0\n\n        </prosody>\n    </voice>\n</speak>'
        t = Trans()  # type: ignore
        l: list[Chapter] = []
        for i in con:
            l.extend(t(i))
        ser = ToServer("Output")
        ser.asyncDownload(l)
        assert l[0].content == rst
        assert len(l[1].content) < 3000


    def test_tts(self):
        con = [
            Chapter(0, "Test title 0", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 0</prosody></voice></speak>'),
            Chapter(1, "Test title 1.mp3", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">'+"甲"*1500+'</prosody></voice></speak>')
        ]
        ser = ToServer("Output")
        ser.asyncDownload(con)


    def test_mer(self):
        if isdir(consts.OPT_DIR+"/test"):
            rmtree(consts.OPT_DIR+"/test")
        copytree("test",consts.OPT_DIR+"/test")
        l = [
            Chapter(1, "test/a (0).mp3", "output"),
            Chapter(1, "test/b.mp3", "output"),
            Chapter(2, "test/c (0).mp3", "output"),
            Chapter(2, "test/b.mp3", "output"),
        ]
        merge(l, False)
        assert isfile(consts.OPT_DIR+"/test/a.mp3")
        assert isfile(consts.OPT_DIR+"/test/c.mp3")
        rmtree(consts.OPT_DIR+"/test")

class TestException:
    def g(self):
        e=PermissionError("Test permissionError")
        ErrorHandler(e,"Test1")()
        ErrorHandler(e,"Test2",level=2)()
        try:
            1/0
        except Exception as e:
            ErrorHandler(e,"Test unknown error",level=3)()
    def f(self):
        self.g()
    def test_exception(self):
        self.f()

if __name__ == "__main__":
    TestUtils().test_mer()