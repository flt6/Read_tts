from log import getLogger
from consts import MAX_RETRY,OPT_DIR
from utils import ToApp,ToServer,Trans,merge,time_fmt
from model import Chapter
from exceptions import ErrorHandler
from traceback import format_exc
from time import time


logger = getLogger("Main")

class Main:
    def __init__(self,type:int,optDir:str):
        self.app=ToApp()
        self.trans=Trans(type)
        self.ser=ToServer(optDir)
        logger.info("Class 'Main' initialized.")
    def dealApp(self):
        logger.debug("Getting shelf")
        shelf=self.app.get_shelf()
        bgn,to,book=self.app.choose_book(shelf)
        chapList=self.app.get_charpter_list(book)
        if chapList is None:
            logger.critical("chapList is None")
            exit(1)
        logger.info("Begin to get Chapers")
        chaps,retry=self.app.download_content(chapList[bgn:to])
        cnt=0
        while len(retry):
            logger.info("Start (New turn) retry.")
            ch,retry=self.app.download_content(retry)
            chaps.extend(ch)
            cnt+=1
            if cnt>MAX_RETRY and len(retry)>0:
                logger.error("Too many retries for Getting shelf")
                logger.error("Articles that failed to download:")
                logger.error(retry)
                break
        logger.info("Request to app finished.")
        return chaps
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
        merge(chaps,True)
        logger.info("merge completed.")
    def __call__(self):
        chaps=self.dealApp()
        chaps=self.textTrans(chaps)
        self.tts(chaps)
        self.merge(chaps)

if __name__ == '__main__':
    try:
        bgn = time()
        main=Main(1,OPT_DIR)
        main()
        end = time()
        t = time_fmt(end-bgn)
        logger.info("Totally used "+t)
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e,"UNCAUGHT",logger,3,True,True)
