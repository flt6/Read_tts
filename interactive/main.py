from model import Book
from log import getLogger
from consts import MAX_RETRY
from utils import ToApp, ConnectServer
from model import Chapter
from exceptions import ErrorHandler
from traceback import format_exc
from time import sleep


logger = getLogger("Main")

class Main:
    def __init__(self):
        self.app = ToApp()
        logger.info("Class 'Main' initialized.")

    def interactive(self):
        logger.debug("Getting shelf")
        shelf = self.app.get_shelf()
        book = self.app.choose_book(shelf)
        if self.typ ==1:
            area= self.app.choose_area(book)
        elif self.typ ==2:
            area= self.app.choose_single(book)
        else:
            e=ValueError("Invalid `typ` %d"%self.typ)
            ErrorHandler(e,"Main",logger,exit=True,wait=True)()
            raise AssertionError("This should never be executed.")
        return book,area
    
    def dealApp(self,book:Book,area):
        chapList = self.app.get_charpter_list(book)
        if chapList is None:
            logger.critical("chapList is None")
            exit(1)
        logger.info("Begin to get Chapers")
        logger.debug(str(area))
        logger.debug(str(len(chapList)))
        logger.debug(str(book.tot))
        chaps, retry = self.app.download_content([chapList[i] for i in area])
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

    def server(self, chaps: list[Chapter]):
        ser = ConnectServer
        # boot
        ser.init()
        ids = []
        l = [chaps[i:][::3] for i in range(3)]
        for sub in l:
            for chap in sub:
                ser.chap(chap)
            assert ser.verify(sub)
            obj=ser.main_start(1)
            if obj is None:
                continue
            ids.append(obj)
            ser.main_clean()
        # wait
        logger.info("Start waiting.")
        end = []
        while len(ids) > 0:
            for id in range(len(ids)):
                ret = ser.main_isalive(ids[id])
                if ret == ser.FINISHED:
                    end.append(ids[id])
                    ids.pop(id)
                    break
                elif ret != ser.RUNNING:
                    logger.error("ret is not RUNNING or FINISHED")
                    logger.info("ret=%d" % ret)
                    ids.pop(id)
            cnt,reasons = ser.get_fail()
            if cnt!=0:
                logger.error("Download failed for %d times"%cnt)
                logger.info("Reasons:")
                for i in reasons:
                    logger.info(i.replace("\\n","\n"))
            ser.progress()
            sleep(5)
        ser.clean()
        # compress
        logger.info("compressing")
        if self.typ == 2:
            fix = True
        else:
            fix = False
        ret = ser.pack(end,fix)
        if ret is None:
            logger.error("Failed to packs")
        else:
            logger.info("Success compress")
        # Output
        logger.info("Retry list:")
        retry=ser.get_retry()
        for chap in retry:
            logger.info("ID: %03d, title: %s"%(chap.idx,chap.title))
        logger.info("For fix mode: %s"% ' '.join([str(i.idx) for i in retry]))
        logger.info("Request Link:")
        logger.info("http://127.0.0.1:8080/pack/getfile")

    def __call__(self, typ: int):
        self.typ = typ
        book,area = self.interactive()
        chaps = self.dealApp(book,area)
        self.server(chaps)


def main(typ:int):
    try:
        main = Main()
        main(typ)
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)

if __name__ == '__main__':
    main(1)
