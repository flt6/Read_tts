from os import path

DEBUG = True
TO_CONSOLE = True

GET_SHELF =        "http://{}/getBookshelf"
GET_CHAPTER_LIST = "http://{}/getChapterList?url={}"
GET_CONTENT =      "http://{}/getBookContent?url={}&index={}"
SERVER =           None

CHOOSEBOOK = '''
No.     %02d
name:   %s
author: %s
now:    %s
-----------------
'''

MAX_RETRY = 5

OPT_DIR = "Output"

if DEBUG is None:
    DEBUG = path.exists("DEBUG")
if SERVER is None:
    assert path.exists("server_ip.conf"), "Const `SERVER` is None, and file `server_ip.conf` does not exists."
    with open("server_ip.conf", "r") as f:
        SERVER = f.read()