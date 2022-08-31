from azure.cognitiveservices.speech.audio import AudioOutputConfig
from aspeak import FileFormat,AudioFormat
from aspeak import SpeechServiceProvider,ssml_to_speech
from log import getLogger

logger = getLogger("TTS")
provider=None
fmt=AudioFormat(FileFormat.MP3,-1)

def init():
    global provider
    logger.info("Start init provider")
    provider=SpeechServiceProvider()
    logger.info("Succeeded.")

def tts(ssml:str,path:str):
    if provider is None:
        init()
    opt=AudioOutputConfig(filename=path)
    return ssml_to_speech(provider,opt,ssml,fmt,True)  # type: ignore