from log import getLogger
from utils import ToApp, ToServer, Trans, merge
from model import Chapter
from os import remove
from os.path import isfile
from tts import tts
import consts


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
    remove("logs/debug.log")
    remove("logs/info.log")
    remove("logs/error.log")


def test_TTS():
    t = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 0</prosody></voice></speak>'
    ret = tts(t, "output.mp3").get()
    assert ret.reason == consts.TTS_SUC


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
        Chapter(1, "Test title 1", 'LongText\n'*625)
    ]
    rst = '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">\n    <voice name="zh-CN-XiaoxiaoNeural">\n        <prosody rate="43%" pitch="0%">\n            Content text 0\n\n        </prosody>\n    </voice>\n</speak>'
    t = Trans()  # type: ignore
    l: list[Chapter] = []
    for i in con:
        l.extend(t(i))
    assert l[0].content == rst
    assert len(l[1].content) < 4400


def test_tts():
    con = [
        Chapter(0, "Test title 0", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 0</prosody></voice></speak>'),
        Chapter(1, "Test title 1", '<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaoxiaoNeural"><prosody rate="43%" pitch="0%">Content text 1</prosody></voice></speak>')
    ]
    ser = ToServer("Output")
    ser.asyncDownload(con)


def test_mer():
    l = [
        Chapter(1, "test/a (0).mp3", "output"),
        Chapter(1, "test/b.mp3", "output"),
        Chapter(2, "test/c (0).mp3", "output"),
        Chapter(2, "test/b.mp3", "output"),
    ]
    merge(l, False)
    assert isfile("test/a.mp3")
    assert isfile("test/c.mp3")
    remove("test/a.mp3")
    remove("test/c.mp3")
