from azure.cognitiveservices.speech import ResultReason  # type: ignore
from os import path

DEBUG = True
TO_CONSOLE = True
SHOW_DBG = False

SSML_MODEL = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-YunyeNeural">
        <prosody rate="43%" pitch="0%">
            {}
        </prosody>
    </voice>
</speak>'''

GET_SHELF = "http://{}/getBookshelf"
GET_CHAPTER_LIST = "http://{}/getChapterList?url={}"
GET_CONTENT = "http://{}/getBookContent?url={}&index={}"

CHOOSEBOOK = '''
No.     %02d
name:   %s
author: %s
now:    %s
-----------------
'''

MAX_RETRY = 5
MAX_TASK = 5
MAX_CHAR = 1500

OPT_DIR = "Output"

TTS_SUC = ResultReason.SynthesizingAudioCompleted

if DEBUG is None:
    DEBUG = path.exists("DEBUG")
if TO_CONSOLE is None:
    TO_CONSOLE = path.exists("SHOW")
if SHOW_DBG is None:
    SHOW_DBG = path.exists("SHOW_ALL")
