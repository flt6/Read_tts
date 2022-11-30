import asyncio

from mytts import AudioOutputConfig, SpeechConfig, SpeechSynthesizer
from mytts.enums import SpeechSynthesisOutputFormat

from log import getLogger
from config import DEBUG

logger = getLogger("TTS")
fmt = SpeechSynthesisOutputFormat.Audio24Khz48KBitRateMonoMp3
cfg = SpeechConfig()
cfg.set_speech_synthesis_output_format(fmt)


def tts(ssml: str, path: str):
    audio_cfg = AudioOutputConfig(filename=path)
    provider = SpeechSynthesizer(cfg, audio_cfg,debug=DEBUG)
    return provider.speak_ssml_async(ssml)._task


def test():
    async def _get(task):
        while not task.done():
            await asyncio.sleep(1)
        
    SSML_text = """<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        wss的v1 接口目
    </voice>
</speak>"""
    future = tts(SSML_text, "t.mp3")
    asyncio.run(_get(future))

if __name__ == "__main__":
    test()
