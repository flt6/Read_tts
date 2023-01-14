from os import path
from mytts import ResultReason


SSML_MODEL = """<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US"><voice name="zh-CN-XiaohanNeural"><prosody rate="18%" pitch="0%">{}</prosody></voice></speak>"""

GET_SHELF = "http://{}/getBookshelf"
GET_CHAPTER_LIST = "http://{}/getChapterList?url={}"
GET_CONTENT = "http://{}/getBookContent?url={}&index={}"



DEFAULT_CONFIG = {
    "MAX_RETRY": 5,
    "MAX_TASK": 10,
    "MAX_CHAR": 1500,
    "WAIT_TIME": 5,
    "RETRY_SUB": 2,
    "MAX_WAIT": 20,
    "TRANS_MODE": 2,
    "TIMEOUT": 3,
    "SHOW_DEBUG": False,
    "bracket": ["“\"'【","”\"'】"],
}

DEFAULT_TYPE = {
    "MAX_RETRY": (int,),
    "MAX_TASK": (int,),
    "MAX_CHAR": (int,),
    "WAIT_TIME": (int, float),
    "RETRY_SUB": (int, float),
    "MAX_WAIT": (int,),
    "TRANS_MODE": (int,),
    "TIMEOUT": (int, float),
    "SHOW_DEBUG": (bool,),
    "bracket": (list,),
}
OPT_DIR="Output"

TTS_SUC = ResultReason.SynthesizingAudioCompleted
TTS_CANCEL = ResultReason.Canceled