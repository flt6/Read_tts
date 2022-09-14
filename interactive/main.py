from log import getLogger
from consts import MAX_RETRY
from utils import ToApp,ConnectServer
from model import Chapter
from exceptions import ErrorHandler
from traceback import format_exc
from time import sleep


logger = getLogger("Main")

class Main:
    def __init__(self):
        self.app = ToApp()
        logger.info("Class 'Main' initialized.")

    def dealApp(self):
        logger.debug("Getting shelf")
        shelf = self.app.get_shelf()
        bgn, to, book = self.app.choose_book(shelf)
        chapList = self.app.get_charpter_list(book)
        if chapList is None:
            logger.critical("chapList is None")
            exit(1)
        logger.info("Begin to get Chapers")
        chaps, retry = self.app.download_content(chapList[bgn:to])
        cnt = 0
        while len(retry):
            logger.info("Start (New turn) retry.")
            ch, retry = self.app.download_content(retry)
            chaps.extend(ch)
            cnt += 1
            if cnt > MAX_RETRY and len(retry) > 0:
                logger.error("Too many retries for Getting shelf")
                logger.error("Articles that failed to download:")
                logger.error(retry)
                break
        logger.info("Request to app finished.")
        return chaps

    def server(self,chaps:list[Chapter]):
        ser=ConnectServer
        # boot
        ids=[]
        l=[chaps[i:][::3] for i in range(3)]
        for sub in l:
            for chap in sub:
                ser.chap(chap)
            assert ser.verify(sub)
            ids.append(ser.main_start(1))
            ser.main_clean()
        # wait
        logger.info("Start waiting.")
        end=[]
        while len(ids)>0:
            ser.progress()
            for id in range(len(ids)):
                ret = ser.main_isalive(ids[id])
                if ret == ser.FINISHED:
                    end.append(ids[id])
                    ids.pop(id)
                    break
                elif ret != ser.RUNNING:
                    logger.error("ret is not RUNNING or FINISHED")
                    logger.info("ret=%d"%ret)
                    ids.pop(id)
            sleep(5)
        # compress
        logger.info("compressing")
        ret=ser.pack(end)
        if ret is None:
            logger.error("Failed to packs")
        else:
            logger.info("Success compress")
        # Output
        logger.info("Request Link:")
        logger.info("http://127.0.0.1:8080/pack/getfile")

    def __call__(self, type: int):
        chaps = self.dealApp()
        self.server(chaps)


if __name__ == '__main__':
    try:
        main = Main()
        main(1)
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)
