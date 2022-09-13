from utils import ToServer,Trans,merge,time_fmt
from model import Chapter
from exceptions import ErrorHandler
from log import getLogger
from consts import MAX_RETRY

from traceback import format_exc
from pickle import load
from time import time
from os import remove
from sys import argv

logger = getLogger("Main")

class Main:
    def __init__(self,type:int,optDir:str):
        self.trans=Trans(type)
        self.ser=ToServer(optDir)
        self.optDir=optDir
        logger.info("Class 'Main' initialized.")
    def textTrans(self,chaps:list[Chapter]):
        logger.info("Trans start.")
        tem=[]
        for chap in chaps:
            tem.extend(self.trans(chap))
        logger.info("Trans completed.")
        return tem
    def tts(self,chaps:list[Chapter]):
        logger.info("tts request started.")
        retry=self.ser.asyncDownload(chaps)
        cnt=0
        while len(retry):
            logger.info("Start (New turn) retry.")
            retry=self.ser.asyncDownload(retry)
            cnt+=1
            if cnt>MAX_RETRY and len(retry)>0:
                logger.error("Too many retries for Getting shelf")
                logger.error("Articles that failed to download:")
                logger.error(retry)
                break
        logger.info("tts completed.")
    def merge(self,chaps:list[Chapter]):
        logger.info("Start merge mp3")
        merge(chaps,self.optDir,True)
        logger.info("merge completed.")
    def __call__(self,chaps:list[Chapter]):
        chaps=self.textTrans(chaps)
        length = len(chaps)
        self.tts(chaps)
        self.merge(chaps)
        return length

if __name__ == '__main__':
    try:
        bgn = time()

        if len(argv)!=2:exit(1)
        file=argv[1]
        with open(file,"rb") as f:
            chaps,optDir,type = load(f)
        remove(file)

        main=Main(type,optDir)
        length=main(chaps)

        end = time()
        t = time_fmt(end-bgn)
        logger.info("Totally used "+t)
        logger.info("Avarage time for each: %ds"%((end-bgn)/length))

    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e,"UNCAUGHT",logger,3,True,True)