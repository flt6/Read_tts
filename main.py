from consts import MAX_RETRY, OPT_DIR, MODE_CHOOSE
from utils import ToApp, Trans, ToServer
from utils import merge, time_fmt, reConcat, redelete
from model import Book, Chapter
from log import getLogger

from exceptions import ErrorHandler
from traceback import format_exc
from shutil import copy
from time import time


logger = getLogger("Main")


class Main:
    def __init__(self, type: int, optDir: str):
        self.app = ToApp()
        self.trans = Trans(type)
        self.ser = ToServer(optDir)
        self.optDir = optDir
        logger.info("Class 'Main' initialized.")

    def interactive(self):
        print(MODE_CHOOSE)
        typ = ""
        while not typ.isdigit():
            typ = input(">>> ")
            if not typ.isdigit():
                print("Invalid mode.")
        typ = int(typ)
        logger.debug("Getting shelf")
        shelf = self.app.get_shelf()
        book = self.app.choose_book(shelf)
        if typ == 1:
            area = self.app.choose_area(book)
        elif typ == 2:
            area = self.app.choose_single()
        elif typ == 3:
            reConcat()
            exit()
        else:
            e = ValueError("Invalid `typ` %d" % typ)
            ErrorHandler(e, "Main", logger, exit=True, wait=True)()
            raise AssertionError("This should never be executed.")
        return book, area

    def dealApp(self, book: Book, area):
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

    def textTrans(self, chaps: list[Chapter]):
        logger.info("Trans start.")
        tem = []
        for chap in chaps:
            tem.extend(self.trans(chap))
        logger.info("Trans completed.")
        return tem

    def tts(self, chaps: list[Chapter]):
        logger.info("tts request started.")
        retry = self.ser.asyncDownload(chaps)
        cnt = 0
        while len(retry):
            logger.info("Start (New turn) retry.")
            retry = self.ser.asyncDownload(list(retry))
            cnt += 1
            if cnt > MAX_RETRY and len(retry) > 0:
                logger.error("Too many retries for Getting shelf")
                logger.error("Articles that failed to download:")
                logger.error(retry)
                for chap in retry:
                    copy("fail.mp3", self.optDir+'/'+chap.title)
                return retry
        logger.info("tts completed.")

    def merge(self, chaps: list[Chapter]):
        logger.info("Start merge mp3")
        merge(chaps, self.optDir, True)
        logger.info("merge completed.")

    def __call__(self):
        book, area = self.interactive()
        chaps = self.dealApp(book, area)
        chaps = self.textTrans(chaps)
        retry = self.tts(chaps)
        if retry is not None:
            print("Retry (for fix mode): " +
                  " ".join([str(i.idx) for i in retry]))
        self.merge(chaps)
        redelete()
        return len(chaps)


def main(typ: int):
    try:
        bgn = time()
        main = Main(typ, OPT_DIR)
        length = main()
        if length == 0:
            logger.info("No chapter requested.")
            exit()
        end = time()
        t = time_fmt(end-bgn)
        logger.info("Totally used "+t)
        logger.info("Avarage time for each: %ds" % ((end-bgn)/length))

    except SystemExit:
        input("Press enter to exit.")
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)()


if __name__ == '__main__':
    main(1)
