# 来源 https://github.com/OS984/DiscordBotBackend/blob/3b06b8be39e4dbc07722b0afefeee4c18c136102/NeuralTTS.py
# A completely innocent attempt to borrow proprietary Microsoft technology for a much better TTS experience
import asyncio
import re
from typing import Optional
import uuid
from datetime import datetime
from time import time

import requests
from websockets.legacy import client

token = None
_token_time = None
EXPIRE_TIME = 3550

def get_token(force_refresh:Optional[bool]=False) -> str:
    global token
    global _token_time
    now = time()
    if token is not None \
        and _token_time is not None \
        and _token_time - now < EXPIRE_TIME\
        and not force_refresh:
        return token
    _token_time = time()
    endpoint1 = "https://azure.microsoft.com/zh-cn/products/cognitive-services/speech-to-text/"
    r = requests.get(endpoint1,verify=False)
    main_web_content = r.text
    # They hid the Auth key assignment for the websocket in the main body of the webpage....
    token_expr = re.compile('token: \"(.*?)\"', re.DOTALL)
    token = re.findall(token_expr, main_web_content)[0]
    return token

# Generate X-Timestamp all correctly formatted
def _getXTime():
    # Fix the time to match Americanisms
    hr_cr = lambda hr: str((hr - 1) % 24)
    # Add zeros in the right places i.e 22:1:5 -> 22:01:05
    fr = lambda x: ":".join(["%02d" % int(i) for i in str(x).split(':')])

    now = datetime.now()
    n = [
        fr(now.year), fr(now.month), fr(now.day), fr(hr_cr(int(now.hour))),
        fr(now.minute), fr(now.second), str(now.microsecond)[:3]
    ]
    return "{}-{}-{}T{}:{}:{}.{}Z".format(*n)

# Async function for actually communicating with the websocket
async def implete(SSML_text:str,opt_fmt:str) -> tuple[str,bytes]:
    req_id = uuid.uuid4().hex.upper()
    Auth_Token = get_token()
    # wss://eastus.api.speech.microsoft.com/cognitiveservices/websocket/v1?TrafficType=AzureDemo&Authorization=bearer%20undefined&X-ConnectionId=577D1E595EEB45979BA26C056A519073
    assert Auth_Token is not None
    endpoint2 = "wss://eastus.tts.speech.microsoft.com/cognitiveservices/websocket/v1?Authorization=" + \
        Auth_Token + "&X-ConnectionId=" + req_id
    # 目前该接口没有认证可能很快失效
    # endpoint2 = f"wss://eastus.api.speech.microsoft.com/cognitiveservices/websocket/v1?TrafficType=AzureDemo&Authorization=bearer%20undefined&X-ConnectionId={req_id}"
    print("Prepare (%s)" % req_id)
    async with client.connect(endpoint2,extra_headers={'Origin':'https://azure.microsoft.com'}) as websocket:
        print("Connect (%s)"% req_id)
        payload_1 = '{"context":{"system":{"name":"SpeechSDK","version":"1.12.1-rc.1","build":"JavaScript","lang":"JavaScript","os":{"platform":"Browser/Linux x86_64","name":"Mozilla/5.0 (X11; Linux x86_64; rv:78.0) Gecko/20100101 Firefox/78.0","version":"5.0 (X11)"}}}}'
        message_1 = 'Path : speech.config\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
            _getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_1
        await websocket.send(message_1)

        payload_2 = '{"synthesis":{"audio":{"metadataOptions":{"sentenceBoundaryEnabled":false,"wordBoundaryEnabled":false},"outputFormat":"%s"}}}'%opt_fmt
        message_2 = 'Path : synthesis.context\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
            _getXTime() + '\r\nContent-Type: application/json\r\n\r\n' + payload_2
        await websocket.send(message_2)

        payload_3 = SSML_text
        message_3 = 'Path: ssml\r\nX-RequestId: ' + req_id + '\r\nX-Timestamp: ' + \
            _getXTime() + '\r\nContent-Type: application/ssml+xml\r\n\r\n' + payload_3
        await websocket.send(message_3)

        # Checks for close connection message
        end_resp_pat = re.compile('Path:turn.end')
        audio_stream:bytes = b''
        while(True):
            response = await websocket.recv()
            if re.search(end_resp_pat, str(response)) is None:
                if type(response) == type(bytes()):
                    # print("recv ({}) {}".format(req_id,response[:5]))
                    try:
                        needle = b'Path:audio\r\n'
                        start_ind = response.find(needle) + len(needle)
                        audio_stream += response[start_ind:]
                    except:
                        print("A part of the audio parsed failed!")
            else:
                break
    return req_id,audio_stream


class Test:
    def __init__(self,SSML_text:str):
        task = self.createTask(SSML_text)
        task.add_done_callback(self._callback)
        asyncio.get_event_loop().run_until_complete(task)
    def createTask(self,SSML_text:str) -> asyncio.Task:
        return asyncio.get_event_loop().create_task(implete(SSML_text,"audio-16khz-32kbitrate-mono-mp3"))
    def _callback(self,future:asyncio.Future):
        ret = future.result()
        print(ret)
        _,b = ret
        with open('output.mp3',"wb") as f:
            f.write(b)

if __name__ == "__main__":
    SSML_text = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        wss的v1 接口目
    </voice>
</speak>'''
    t = Test(SSML_text)
