from multiprocessing import Process
from requests import get
from json import loads
from traceback import format_exc
from log import Log
import re
from consts import DEBUG,SSML_MODEL
from os import path,mkdir,system,getpid
import tts
from sys import exit
from utils import *


# logger = Log("Main",debug=DEBUG,show=True).get_logger()
logger = getLogger("main")