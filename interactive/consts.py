from os import path

DEBUG = True
TO_CONSOLE = True

GET_SHELF="http://{}/getBookshelf"
GET_CHAPTER_LIST="http://{}/getChapterList?url={}"
GET_CONTENT="http://{}/getBookContent?url={}&index={}"

CHOOSEBOOK='''
No.     %02d
name:   %s
author: %s
now:    %s
-----------------
'''

MAX_RETRY= 5

OPT_DIR="Output"

if DEBUG is None:
    DEBUG=path.exists("DEBUG")
