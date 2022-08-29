from log import getLogger
from consts import MAX_RETRY,OPT_DIR
from utils import ToApp,ToServer,Trans
from model import Chapter


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
        for chap in chaps:
            chap=self.trans(chap)
        logger.info("Trans completed.")
        return chaps
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
    def __call__(self):
        chaps=self.dealApp()
        chaps=self.textTrans(chaps)
        self.tts(chaps)

if __name__ == '__main__':
    main=Main(1,OPT_DIR)
    main()
