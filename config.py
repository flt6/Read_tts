import json
from os.path import exists
from typing import Any, Union

from consts import DEFAULT_CONFIG, DEFAULT_TYPE

MAX_RETRY : int
MAX_TASK  : int
MAX_CHAR  : int
WAIT_TIME : Union[int,float]
RETRY_SUB : Union[int,float]
LIMIT_429 : int
MAX_WAIT  : int
FAIL_429  : int
TIMEOUT   : Union[int,float]
OPT_DIR   : str
DEBUG     : bool
TO_CONSOLE: bool

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
            json.dump(DEFAULT_CONFIG,f)
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


if __name__ == "__main__":
    check()
    print("Config is valid.")
else:
    globals().update(load())