from mytts import ResultReason  # type: ignore

SSML_MODEL = """<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaohanNeural">
        <prosody rate="18%" pitch="0%">
            {}
        </prosody>
    </voice>
</speak>"""

GET_SHELF = "http://{}/getBookshelf"
GET_CHAPTER_LIST = "http://{}/getChapterList?url={}"
GET_CONTENT = "http://{}/getBookContent?url={}&index={}"

MODE_CHOOSE = """\
Choose running mode:
1. Basic
2. Fix
3. Concat
4. Delete temporary files
"""

CHOOSEBOOK = """
[b bright_red]No.     %02d[/b bright_red]
[orange1]name:   %s[/orange1]
[chartreuse3]author: %s[/chartreuse3]
[bright_cyan]now:    %s[/bright_cyan]
"""


DEFAULT_CONFIG = {
    "MAX_RETRY": 5,
    "MAX_TASK": 10,
    "MAX_CHAR": 1500,
    "WAIT_TIME": 5,
    "RETRY_SUB": 2,
    "LIMIT_429": 0.7,
    "MAX_WAIT": 20,
    "FAIL_429": 3,
    "TIMEOUT": 3,
    "OPT_DIR": "Output",
    "DEBUG": False,
    "TO_CONSOLE": True,
    "LANG_FILE": "lang_zh.json",
}

DEFAULT_TYPE = {
    "MAX_RETRY": (int,),
    "MAX_TASK": (int,),
    "MAX_CHAR": (int,),
    "WAIT_TIME": (int, float),
    "RETRY_SUB": (int, float),
    "LIMIT_429": (float,),
    "MAX_WAIT": (int,),
    "FAIL_429": (int,),
    "TIMEOUT": (int, float),
    "OPT_DIR": (str,),
    "DEBUG": (bool,),
    "TO_CONSOLE": (bool,),
    "LANG_FILE": (str,),
}


TTS_SUC = ResultReason.SynthesizingAudioCompleted
TTS_CANCEL = ResultReason.Canceled
