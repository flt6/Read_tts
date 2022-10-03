from consts import MODE_CHOOSE
from config import MAX_RETRY, OPT_DIR, WAIT_TIME,RETRY_SUB, MAX_TASK
from config import check
from utils import ToApp, Trans, ToServer
from utils import merge, time_fmt, reConcat, redelete
from model import Book, Chapter
from log import getLogger

from exceptions import ErrorHandler
from traceback import format_exc
from shutil import copy
from time import sleep, time
from sys import exit


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
        if typ == 3:
            reConcat()
            exit()
        elif typ == 4:
            redelete()
            exit()
        self.app.init()
        logger.debug("Getting shelf")
        shelf = self.app.get_shelf()
        book = self.app.choose_book(shelf)
        if typ == 1:
            area = self.app.choose_area(book)
        elif typ == 2:
            area = self.app.choose_single()
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
        retry = self.ser.asyncDownload(chaps)  # type: ignore
        cnt = 0
        max_task = MAX_TASK
        while len(retry):
            logger.info("Start retry waiting.")
            sleep(WAIT_TIME)
            max_task//=RETRY_SUB
            if max_task < 1: 
                max_task = 1
            logger.info("Start (New turn) retry.")
            retry = self.ser.asyncDownload(list(retry),max_task)
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
        self.merge(chaps)
        if retry is not None:
            retry = set(retry)
            logger.info("Retry (for fix mode): " +
                  " ".join([str(i.idx) for i in retry]))
            k = len(retry)/len(chaps)
            if k > 0.7:
                logger.info("There are too many instances needed to retry for 5 times")
                logger.info("Retry/Total: %.2f%%"%k*100)
                logger.info("You may need to decrease the muliple requests number (`MAX_TASK` in config.json)")
        redelete()
        return len(chaps)


def main(typ: int):
    try:
        check()
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

    except SystemExit as e:
        logger.info(f"SystemExit with code {e.code} got, may exit not normally.")
        return
    except KeyboardInterrupt:
        logger.info("Got keyboard interrupt, exit forcely.")
        return
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)()


if __name__ == '__main__':
    main(1)
    input("Press enter to exit.")
