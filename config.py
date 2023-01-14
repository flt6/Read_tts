import json
import bz2
from base64 import b64encode,b64decode
from rich import print
from os.path import exists
from typing import Any, Union

from consts import DEFAULT_CONFIG, DEFAULT_TYPE

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
    with open("config.json", "w",encoding="utf-8") as f:
        json.dump(new,f)
    globals().update(new)

def check():
    typ: dict[str, tuple] = DEFAULT_TYPE
    if not exists("config.json"):
        print("config.json is not found. Auto created.")
        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f)
    with open("config.json", "r", encoding="utf-8") as f:
        d: dict[str, Any] = json.load(f)
    suc = True
    for key in d.keys():
        to = typ[key]
        if not type(d[key]) in to:
            print(f"The type {key} is {type(d[key])} but {to} expected.")
            suc = False
    if not suc:
        print("Config is invalid.")
        exit(1)

def setup():
    with open("lang_en.json", "r", encoding="utf-8") as f:
        obj = bz2.compress(f.read().encode())
    print(b64encode(obj))
    with open("lang_zh.json", "r", encoding="utf-8") as f:
        obj = bz2.compress(f.read().encode())
    print(b64encode(obj))

lang_zh = b"QlpoOTFBWSZTWfb1oMcAAe7f+VAQUuX+MCBqTkD/999uf//////f7/+P4NADfpFAALARNBNKeFNpPUAekGRoNG1GQNHqNND0QGmgAABoAAAGg1FNPU9JqZkZqaGptTIZMI2UDRoAaAAAAAAAAAAIMAAAAAAAAAAAAAAAAAAAAAgwAAAAAAAAAAAAAAAAAAAAAkSTU0yTaSeQnkTJqeJPTKPSeo9Gp6g0aaHkg0eiAaB6g0aHqNG1DabRRJAjbrQNoVoYENtDjcVCQkqUJGWKAQIQAniEGoSQxAQEVaVwQPHEWrWNBdeWWU13z07qczZK1R9epVbaoxzbgwV2S8524Z4z2PNmJr3BcQ+OWJpZUoVBMx9YFECBhZtGN2vJ2FfY002MbiFCG2ggEHRLpCNEvxnUYupseaIB9PauFhna8jxVdjEO8yDbCvrFtzm7VkOrfzwweH8NykKmNoG0g/f4zVw+VMJ5fs9npT4Pa3tnsm77cq6KpVx31wbTeAR2cLq8WOYClzhJDoEOdQhzghQql1g5pqDoEJpFC/WSXwEj6efgfcojY135nUNz1G8MDbbpw1K9kYQvWlNafOxO2qbDIptptsbCJD37H6pXTv1HPgSz3QXDbzL6umZYguNGXWorrTXoymLMUFE3aJDVGA1C5JZeBYL6mWzoVlEaLelNWFF5Up0l4KCFmX4uNzO5UFV1PJM+0rbMhQdCS1rcXsgsay1bOkHb/X1olD5OM5YPGjh8C/3tLvP144HxRRVEu/cPD7xjN7tR1jmRHCj6FdESEZXffyIcnlssUkc2Y+JY9yPI5stBi7y/u41QXi7hxY7mazuo4ZUXyusMCMqSDNqvLdVCT7Yxcp40d1lvN4LCy/PkhkgNHxSHjCKBYVxNjHxySpYZOOGRJYIylYYqDKLStkkMdJRIYa00mar8lT/NLGqs8X6U9NaNxK7zi8IxaGT97tw3BrzuhTpfMoSq8vVZmWKODkInpZzpVFOmRx3FQWtSQPQKZ5KU3+2ns6E/PkSZSWXlAfjwpaeQqMZoVk5yNKWaxmt0UPmErpnQr6o9DEUUNtsvNE9onNH/JNNYoyQ5C3BssIYMw9XBteD+r9/8urP2K97U7HLqBnqOFhRI0R4nzCav6VKT/Imzr2nZQCQVEAkSXgFtgdPGgBIEhVDCvEeTGhu3DBU4j7amMZtA7N3TC+GKRAV8EHav5kkyApTqKECLcs+F+GDpFDJBtIWovQGnSS05zQ5NKkYVUWUsUpJojoevYdmKITpMn/ch+265GAsE5DjLiJE/OgJNLFiMQXYRFWv6apYtznlTFjA5YJAmrAzCUDmO8eKllP3spCgZXqzuIHT5RbpYGQokkW2lkIrNXLRf+ldTR/i7kinChIe3rQY4"
lang_en = b"QlpoOTFBWSZTWcjfUdAAA3zfgFAQUuX+Mj7rXmD////+UANdbq1Xu1ytxOhKEJoUw0METBAGmQAAGgA0KeSYmSamajaTIGmhoAAANPUNBpkQQKejJJ+pPRqaGTRoPUBoGmQPUDalI0AAA0AAAAAAABKahGmlP1Mpo9R5QaAABoADQGg+EhfIgkzCICZJOMzCZz8PwQEEQLPQEA5UVU/NjHwONu1q7Pd91GJHJ/TXKcce+U1tePhzyEFSqEMC+upHLVCGGAZexhO+P9XSH1alTKYZo79CfIaJGo6i4sGBT8LdAJcw8vTdu6ueK112Vl31QcwrXAkdpYslactEeNVr3NV4tGGyvHIPg8feRliIihIycoutPFKwEG6wWByKJTJiQQSkCUwJIZAseMZBMPYrEZbr0GRSdWK97VyiALhjRlUi9kdxwcb/JgKTdl4s5DHv5ickgd4F3Oz3yUxsRW4Dx4GBAIAYkASVVasOeQKpJ5vXz0xRHigoouZjm12dL/KfR2e0ERzrg4X8lPtDXH5Fp1WYbTuPTedyWwutC3L0NETaIaU5jt8FkZSVR+8owkNn2bIBl0n6GX1HvrCTG+D4jrKyEQTJQ1L2flfich7S3+bGOGwRaNJ7CPLSDAsIlM4IWn1CA8MQBYkSTXQCrmMLmcTpr9GWWp89n8nF9ZcYg6DkineuAqA+qylx0DWczuUB0Bm+pRgWIrSnW48M+c9NUVnUxPwrCNuWmVi5YlkAdfFFVPo+6b5ImYtKytRRRYMqo5keqW5sUC3FkvmUmdBaQ0C4ycNVEzzABVnUgApLLGoyMHM8GLRsydpFSleIW+AihSNadGixAoexnrNOPZATHkgipMF+ZkW80dwskLEUjB6OagoOcWLo8hFjeGHIcXht+DVEmmzdqa2BgrAJ2SkPIMa5uIJCJmRsUaGx4Fye5oZBOGlUm4ri1E4EwpM+1hjFMtqfzpUE6aWf0o28B14XOQOSYiyeWEzYhDWv1aiw0U1DRJSoLoBGsLXkcQma8WpATl336WvqU2wojjeIljF3Eg78KNcwzattWiwSeUY9DGtJW5uUUEA9swH6wWpZQih2XCIxcahRMBYUwqCBAJEzBhBzKA6lO6t9Ztl1lnzXWtgE5wDAbQsxrx2Jv9AFxrQ7XJTFrxW8Dge5JH/i7kinChIZG+o6AA=="

def load_lang() -> dict:
    try:
        if LANG_FILE == "lang_zh.json":
            lang = bz2.decompress(b64decode(lang_zh)).decode()
        elif LANG_FILE == "lang_en.json":
            lang = bz2.decompress(b64decode(lang_en)).decode()
        else:
            with open(LANG_FILE, "r", encoding="utf-8") as f:
                lang = f.read()
        return {"lang": json.loads(lang)}
    except FileNotFoundError:
        print("File `lang.json` not found!")
        exit(-1)
    except json.JSONDecodeError:
        print("`lang.json` is invalid!")
        exit(-1)


if __name__ == "__main__":
    check()
    print("Config is valid.")
    setup()
else:
    globals().update(load())
    globals().update(load_lang())
