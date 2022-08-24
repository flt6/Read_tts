from aspeak import FileFormat
from aspeak import SpeechServiceProvider,ssml_to_speech
from azure.cognitiveservices.speech.speech import  ResultFuture
from azure.cognitiveservices.speech.audio import AudioOutputConfig
from consts import SSML_MODEL
fmt=FileFormat.MP3
print(1)
provider=SpeechServiceProvider()
print(1)
l=[]
for i in range(30):
    opt=AudioOutputConfig(filename=f"test{i}.mp3")
    art=f"{str(i)*50}中{i}文12as1fas1fas1fas1fas1fas1fas1fas1fas1fas1fas1f2sd1f3s{i}d1f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f31f3ds{i}文本测试."
    l.append(ssml_to_speech(provider,opt,SSML_MODEL.format(art),fmt,True))  # type: ignore
for i in l:
    print(i.get())