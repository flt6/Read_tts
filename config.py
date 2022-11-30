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
LIMIT_429: int
MAX_WAIT: int
FAIL_429: int
TIMEOUT: Union[int, float]
OPT_DIR: str
DEBUG: bool
TO_CONSOLE: bool
LANG_FILE: str
lang: dict[str, dict]


def load():
    config = DEFAULT_CONFIG.copy()
    if exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            d = json.load(f)
        config.update(d)
    return config


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

lang_zh = "QlpoOTFBWSZTWUVqvsYAAe9f+VAQUuX+MCBqTkD/998uf//////f7/+P4NADfpFBQC2gaJNBTaJkxAGhpo0GjI0ZA00aMTRoyADQAZBpoAAyERFP1T9CmepHmoyj0j0I2k0PSAYgAYQaAxBkAANGgZNGgOAAAAAAAAAAAAAAAAAAAAAHAAAAAAAAAAAAAAAAAAAAABIoSZNDIE0ymp7RTzVNk1NqehqemoGjIPUBjUeoDIAGmj1A9IxtJEUCN6lA2hWBgQbaHDfUkhJToSNBEAwRAa5iwcrkoQVD9plcjfyitLRrNZZj02HFScxxLzN9Dil7dzDTgpQVKBumWyKKXd4mBGjy5C9u8N4rKOSamehdVgLyJTQLKmFDbPWvBTd21fY002MbhBQQ20EAQahcIBqjvvSlk87b6IgHs7toqNK9tSP7p6+Qd1kDqha3lKTmrg6OHTDD9+/YChibQ2kHH5nE8erME2H1+xmm+z2ODc7B7XsxplZjjTJZDpfDBQZZwWX8FQIRqGT2eSUrElIVWQthRJik+ECKcgOaSK7JE7mjgfDKHR6D2ukdP0m8cBttz47Krt4wrsKZa97I6FPUW56E22NhCNUO3W/TLVHbpNGAlpuqYuG9iwKoxVoLbRitKFNKZcfVkWBaKgSsOciNS0DMW4q7gWDApig8qklDVb1plUSrU6c5WEiC7V/BG23YOGkKak7xlsKhlxQMsVtUQu20YlOc8Oz3/VhGD5fEc0Dwo/bvF8TC4T0Ecx+qE1yFOtkeM0fomRKpBSmQqUCbEAkEHdE94BxegypRR5MT5Fn9GHjczLAZO6vBaakVlzHkz2ucziRxxlfppDAjDFBpWa17akLtEBcx4UcTKOd91SqvzPlIgeXyRHnCEhY14Gxj14pTtF3PBkIrBDCqjJIwlhUEUMZOSiMNmZJmw/HZfeSzqzpi78+ytW0lcvFYjJlu8bog3A2prgT63zKCVnn7DMVSh9vKoTa2k51KfXIeK0pFjNFPKT3UpPj1+llm6cSLLRVWoBh/H90te4ps5ltExNE1o2WM6Goh+QSuGlBXwljIxbbZU0S3SaZH/JNNY4VhylEDcYQYM0d2/1P05L2/+fnzdengzetzZj3VrhDx9AfRi+3jjIrVqqZUuE2aqiKGDAh48YG6anPzm4hmSFlXwuWmLjDjrDSe6ZaTZ52CkvmZQLSgjiAdqD0rMNohDgnJ1CCBbIHFr7kxuKUDTtHUPUDJuLNRs5D8O7vTFrR1K21sLJhlK90jbKN58X9bTjOLgEMrLjjxVm/2XSLBhnVdxrcRmP6IpgMxENKUwBRuxAkZ1OFFKQqCBhtJ2jR1AfKwiuHDw9l5LwCHURRHjXwhGbVHhJ1oUg/+LuSKcKEgitV9jA=="
lang_en = "QlpoOTFBWSZTWcjfUdAAA3zfgFAQUuX+Mj7rXmD////+UANdbq1Xu1ytxOhKEJoUw0METBAGmQAAGgA0KeSYmSamajaTIGmhoAAANPUNBpkQQKejJJ+pPRqaGTRoPUBoGmQPUDalI0AAA0AAAAAAABKahGmlP1Mpo9R5QaAABoADQGg+EhfIgkzCICZJOMzCZz8PwQEEQLPQEA5UVU/NjHwONu1q7Pd91GJHJ/TXKcce+U1tePhzyEFSqEMC+upHLVCGGAZexhO+P9XSH1alTKYZo79CfIaJGo6i4sGBT8LdAJcw8vTdu6ueK112Vl31QcwrXAkdpYslactEeNVr3NV4tGGyvHIPg8feRliIihIycoutPFKwEG6wWByKJTJiQQSkCUwJIZAseMZBMPYrEZbr0GRSdWK97VyiALhjRlUi9kdxwcb/JgKTdl4s5DHv5ickgd4F3Oz3yUxsRW4Dx4GBAIAYkASVVasOeQKpJ5vXz0xRHigoouZjm12dL/KfR2e0ERzrg4X8lPtDXH5Fp1WYbTuPTedyWwutC3L0NETaIaU5jt8FkZSVR+8owkNn2bIBl0n6GX1HvrCTG+D4jrKyEQTJQ1L2flfich7S3+bGOGwRaNJ7CPLSDAsIlM4IWn1CA8MQBYkSTXQCrmMLmcTpr9GWWp89n8nF9ZcYg6DkineuAqA+qylx0DWczuUB0Bm+pRgWIrSnW48M+c9NUVnUxPwrCNuWmVi5YlkAdfFFVPo+6b5ImYtKytRRRYMqo5keqW5sUC3FkvmUmdBaQ0C4ycNVEzzABVnUgApLLGoyMHM8GLRsydpFSleIW+AihSNadGixAoexnrNOPZATHkgipMF+ZkW80dwskLEUjB6OagoOcWLo8hFjeGHIcXht+DVEmmzdqa2BgrAJ2SkPIMa5uIJCJmRsUaGx4Fye5oZBOGlUm4ri1E4EwpM+1hjFMtqfzpUE6aWf0o28B14XOQOSYiyeWEzYhDWv1aiw0U1DRJSoLoBGsLXkcQma8WpATl336WvqU2wojjeIljF3Eg78KNcwzattWiwSeUY9DGtJW5uUUEA9swH6wWpZQih2XCIxcahRMBYUwqCBAJEzBhBzKA6lO6t9Ztl1lnzXWtgE5wDAbQsxrx2Jv9AFxrQ7XJTFrxW8Dge5JH/i7kinChIZG+o6AA=="

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
else:
    globals().update(load())
    globals().update(load_lang())
