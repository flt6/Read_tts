import json
from os.path import exists
from typing import Any
from consts import DEFAULT_CONFIG, DEFAULT_TYPE


MAX_RETRY  : int
MAX_TASK   : int
MAX_CHAR   : int
OPT_DIR    : str
DEBUG      : bool
TO_CONSOLE : bool


def load():
    config = DEFAULT_CONFIG.copy()
    if exists("config.json"):
        with open("config.json", "r", encoding="utf-8") as f:
            d = json.load(f)
        config.update(d)
    if config["DEBUG"] is None:
        config["DEBUG"] = exists("DEBUG")
    return config


def check():
    typ: dict[str, tuple] = DEFAULT_TYPE
    if not exists("config.json"):
        print("config.json is not found.")
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