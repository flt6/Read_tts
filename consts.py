from os import path
from azure.cognitiveservices.speech import ResultReason

DEBUG = True
TO_CONSOLE = True

SSML_MODEL = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        <prosody rate="43%" pitch="0%">
            {}
        </prosody>
    </voice>
</speak>'''

GET_SHELF="http://{}/getBookshelf"
GET_CHAPTER_LIST="http://{}/getChapterList?url={}"
GET_CONTENT="http://{}/getBookContent?url={}&index={}"

CHOOSEBOOK='''
No.     %02d
name:   %s
author: %s
now:    %s
-----------------
'''

MAX_RETRY=5

OPT_DIR="Output"

TTS_SUC=ResultReason.SynthesizingAudioCompleted

if DEBUG is None:
    DEBUG=path.exists("DEBUG")
