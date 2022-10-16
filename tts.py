from aspeak import AudioFormat, FileFormat, SpeechToFileService

from log import getLogger

logger = getLogger("TTS")
provider = None
fmt = AudioFormat(FileFormat.MP3, -1)


def init():
    global provider
    logger.info("Start init provider")
    provider = SpeechToFileService(locale="zh-CN", audio_format=fmt)
    logger.info("Succeeded.")


def tts(ssml: str, path: str):
    if provider is None:
        init()
    return provider.ssml_to_speech_async(ssml, path=path)  # type: ignore
