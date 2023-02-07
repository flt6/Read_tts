import json
import bz2
from base64 import b64encode,b64decode
from rich import print
from os.path import exists
from typing import Any, Union

from consts import DEFAULT_CONFIG, DEFAULT_TYPE, OLD_DATA_TRANSFORM

MAX_RETRY: int
MAX_TASK: int
MAX_CHAR: int
WAIT_TIME: Union[int, float]
RETRY_SUB: Union[int, float]
MAX_WAIT: int
TRANS_MODE: int
TIMEOUT: Union[int, float]
OPT_DIR: str
SAVE_LOG: bool
SHOW_DEBUG: bool
SAVE_REQ: bool
TO_CONSOLE: bool
bracket: list[str]
LANG_FILE: str
ip:str
lang: dict[str, dict]


def load():
    config = DEFAULT_CONFIG.copy()
    if exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            d = json.load(f)
        config.update(d)
    return config

def update(data:dict[str,Any]):
    with open("config.json", "r",encoding="utf-8") as f:
        new:dict[str,Any] = json.load(f)
    new.update(data)
    _update(new)

def _update(data:dict[str,Any]):
    with open("config.json", "w",encoding="utf-8") as f:
        json.dump(data,f)
    globals().update(data)

def check():
    if not exists("config.json"):
        print("config.json is not found. Auto created.")
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f)
    with open("config.json", "r", encoding="utf-8") as f:
        d: dict[str, Any] = json.load(f)
    typ: dict[str, tuple] = DEFAULT_TYPE
    suc = True
    for key in d.keys():
        # Transform old config to new config.
        if key in OLD_DATA_TRANSFORM.keys():
            if not OLD_DATA_TRANSFORM[key](d):
                print(f"The old '{key}' can't be transformed!")
                suc = False
                continue
            else:
                print(f"The old config '{key}' transformed by automatic.")
                update(d)
                check()
                break
        to = typ[key]
        if not type(d[key]) in to:
            print(f"The type of '{key}' should be {type(d[key])} but {to} expected.")
            suc = False
    if not suc:
        print("Config is invalid.")
        exit(1)
    return d

def setup():
    print("---------en-----------")
    with open("lang_en.json", "r", encoding="utf-8") as f:
        obj = bz2.compress(f.read().encode())
    print(b64encode(obj))
    print("---------zh-----------")
    with open("lang_zh.json", "r", encoding="utf-8") as f:
        obj = bz2.compress(f.read().encode())
    print(b64encode(obj))

lang_zh = b'QlpoOTFBWSZTWVr2QZ0AAf1f+VAQUuX+MCBqTkr/999uf//////f//+P4NAD3pEhQAsHEEI1GRMCDIaDQZGmENAyDQZGmhiAaNABoAGgGjIIhKbJiaaaaYmpmoyejU0aNHqbSMnqNNDQDRpoAAAAAAAGiDTEwAAAAAAAAAAAAAARhGAAAAEGmJgAAAAAAAAAAAAAAjCMAAAACRQQgAT0ozJpPSMKYah4oepoyeppoeoAaADR6g0aMjTRoGnlMSIhG9ZQNiVAwINtDh0VISSVIkitKAQCIBNIGzdInEFAfLRuJp6R1rJlqrryDRmvlNTRTL3TNaXunswV6FKEffJuyrjdKHL1EDKkyNHPYWjwniiSkkeQZKjAE50pYFVCA5M9W3wWb+0N4WNNNjG4QUENsRAEHKLhBGcwwyS0fH2ugkA/G3bRdMm/z5H8WeppDvsgbwWvMKnObovQdjrZg0P27HRpRYY2gbSDufEbOjqzCdfp9XXn9nqet5PVOD1TrIYndIlLg4S2PphCAYksojN9DOBjTCF7PFCFRQgFFTKmgY0xE+IAjOMDZYTjNA4UXWthV59dU0PAKDECNlETswERESXbEcFvSDBQprYxaTqVN0t01JtsbCER5rr6ZZp61g0YCWo5FojvY8KuGO6gtNFdpQtWk15sZixqBKboURqWI2C1FV4liwqZYsGaBKGq3rTV0leVKdKvBIgseGFpsme/YCxcTvmnKhVNW1AyxXPsQvWy61WqjZD3e3vwOYq37UGsYPmh9iHj2iiYKhZpuUvYyDsTgikozZB+UqYU5wVQ1O17kfX3+mXESP1FwqGgIaRpdp9dDjihkZAIo8OUqhoLwdKHG6GVVBms8Kf9NNSLZczangt6bD40d2MsRZshC8jQ+uYjTs3wyqST+EYuWf4jlMqydi6i9inxQZEDP3o/9fhGIQmBorZbGPvxAqYYMpxkRkZKuFtXjJJV4HSrASQzihYJ3pqAcW1Ukzm8UJXH2wOMLWcXcp5wcy2lhvVmERHPg7Lqg3A6E7gUmv11EilKxk5rMd0OR35cMVCjmZnUEqtYhuXAkUa8QeoUzviJjXO19vUmcncjIbKi9fW1FHZ7qWtdWxPZM9sooia0dRjKsLwIfhSWJrk4DLFSVdG46Sc23W4PbZiaKN1umFCPEkNDWSGgFOqOBtygEWDMtGXkVbp+XL72Ovxfj5Hl1dS9wPpFW2CYrcPDnuX8F/dC4qWrfERWi1YDpMmVBatFHJLAuQBhxY4FYtB1kUgcGIi5hYSQKj2OQm3PUGasZsSoWbdGLOugn74wWQgkkegsaxSlLTGbx6uCLVNAQL0Bgpcoq9BgIifFlBHKBmAFIAsmxWpstEOPRvq5YIOxGoKZCCghFVx3jxSuzIBOaCDr85avUQZnOMCCWbHcYtsqrRMipN1kSrSCOevMhnz6qoBGUkEbQcafEzKjAGDy0QFGSA8b80M8U44s4hIA2j7BqGeE3FiqyDaEMOnziU0geLHFFDo3AhQG4Q6BsmNwNl00Er7F3JFOFCQWvZBnQA=='
lang_en = b'QlpoOTFBWSZTWf27vqgAA5DfgFAQUuX+Mj7r3ur////+UAN6yyGzI2zWhppBNEyepqeE1T9TNSPU000emkeoH6oaaY9FHqaDSYQ0k0jT1B6mjJo0NABoAANBoEiTUaI0NTTTamkDQ0GIekAAABocwJiaDCZMmTIwmCaaZGJgCGA5gTE0GEyZMmRhME00yMTAEMFBCP7mQNiVowIbaHHWpEklUSR6NokAwoSnL4qMgwcOC26fJtCKHsTzl7aLL4fiUbliMmNDnQO476K+mY4rU72OGXKwr+6Z7shOrMp7MAzU20P4DUKCjJBA4rgaZ6WgNgGPeqw5MSzneebfMzCQU6IB6xPYghesV2szdbWxw4fwWCqnPdOISwHG9zZhMGLNCeRw9FhqfiIXSMT1uG4UJsY3EDcIbaUDT2mshG9wVu0SiEzM4Nve6ehIB6649plZhU8VlDv+PgNg54eUa3jRlrJqVQd4E/pRlDleLFK4AbKC0NBACEoA+23bV0PAtfNL2d3qkRGggNUKD++hg3dt3X9/m/v/U/Tj4P8SEa2kMFPjhKJvB6aD3FICZc54i8JhkezQelVvLFwKbNqNa9GtRz3k5X6JJZTAf7eEBITl687QMamZscgxKEHIcQCSB3aBZAVkoaU2nhnZG/lVLY/ns0Bx6QuNhV8MXLqGGtKW74XV6SSkpgXxDbd24LqOdGdULa8PVs1404tvLbOF1nES6PCJe+dSoXZ8a2uh1s0ckgfKMOM80EqStKM7zzUbzsskMxFTeYuku1VwUT6U0uAZEEEp/R1VxD01i4Wi0ggguUlGKjSl2upwuqviNRfSx7A7o9xmDpxvk4Az80oCVOGUm6wtsuGbDiwtOczyv4X7PeZoWDmvNzZIMZg7e05d2+wW7ksTV4ar4T0xXOZWmSZWyVSMXBR6k6Q+Nl63TRlDAXmrKYYokXuZUUVm5CLs4QKQvjFABxAXBgKuTFetFZYqN1gqElgU6qxEidonAeOWF1InUiMGbiXCd9qpvZ3OMjINkMIbRVOhpMF2JndltuNJi1Yql99hskK5g1UK6BpZD4pIo6U8mWamMWrRWGasCbNS1XTCJnkVRCwp0mSuGRl0MZQnJqWJA4GDASkQE5xqt9WVezOTOqhiV00QYrSWQsyCM7YyDokD4LjGES7n802arrHRFFEocBeFrFMbFTFoGYwkN7CYTWBdgH+f3iIf/F3JFOFCQ/bu+qA='

def load_lang() -> dict:
    try:
        if LANG_FILE == "zh":
            lang = bz2.decompress(b64decode(lang_zh)).decode()
        elif LANG_FILE == "en":
            lang = bz2.decompress(b64decode(lang_en)).decode()
        else:
            with open(LANG_FILE, "r", encoding="utf-8") as f:
                lang = f.read()
        return {"lang": json.loads(lang)}
    except FileNotFoundError:
        print(f"File `{LANG_FILE}` not found!")
        exit(-1)
    except json.JSONDecodeError:
        print("`{LANG_FILE}` is invalid! Please check if it is a correct json file.")
        exit(-1)



if __name__ == "__main__":
    check()
    print("Config is valid.")
    setup()
else:
    print("Checking configurations...")
    check()
    globals().update(load())
    globals().update(load_lang())
