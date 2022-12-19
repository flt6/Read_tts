from shutil import copy
from sys import exit
from time import sleep, time
from traceback import format_exc

from config import (MAX_RETRY, MAX_TASK, OPT_DIR, RETRY_SUB,
                    WAIT_TIME, TRANS_MODE, check, lang)
from consts import MODE_CHOOSE
from exceptions import ErrorHandler
from log import getLogger
from model import Book, Chapter
from utils import ToApp, ToServer, Trans, merge, reConcat, redelete, time_fmt

logger = getLogger("Main")


class Main:
    def __init__(self, type: int, optDir: str):
        self.app = ToApp()
        self.trans = Trans(type)
        self.ser = ToServer(optDir)
        self.optDir = optDir
        logger.info(lang["main"]["init"])

    def interactive(self):
        print(MODE_CHOOSE)
        typ = ""
        while not typ.isdigit():
            typ = input(">>> ")
            if not typ.isdigit():
                print(lang["main"]["mode_invalid"])
        typ = int(typ)
        if typ == 3:
            reConcat()
            exit()
        elif typ == 4:
            redelete()
            exit()
        self.app.init()
        logger.debug(lang["main"]["shelf"])
        shelf = self.app.get_shelf()
        book = self.app.choose_book(shelf)
        if typ == 1:
            area = self.app.choose_area(book)
        elif typ == 2:
            area = self.app.choose_single()
        else:
            e = ValueError(lang["main"]["typ_invalid"] % typ)
            ErrorHandler(e, "Main", logger, exit=True, wait=True)()
            raise AssertionError("This should never be executed.")
        return book, area

    def dealApp(self, book: Book, area):
        chapList = self.app.get_charpter_list(book)
        if chapList is None:
            logger.critical("chapList is None")
            exit(1)
        logger.info(lang["main"]["chap"])
        logger.debug(str(area))
        logger.debug(str(len(chapList)))
        logger.debug(str(book.tot))
        chaps, retry = self.app.download_content([chapList[i] for i in area])
        cnt = 0
        while len(retry):
            logger.info(lang["main"]["retry_st"])
            ch, retry = self.app.download_content(retry)
            chaps.extend(ch)
            cnt += 1
            if cnt > MAX_RETRY and len(retry) > 0:
                logger.error(lang["main"]["fail1"])
                logger.error(lang["main"]["fail2"])
                logger.error(retry)
                break
        logger.info(lang["main"]["app_suc"])
        return chaps

    def textTrans(self, chaps: list[Chapter]):
        logger.info(lang["main"]["trans_st"])
        tem = []
        for chap in chaps:
            tem.extend(self.trans(chap))
        logger.info(lang["main"]["trans_end"])
        logger.debug(tem)
        return tem

    def tts(self, chaps: list[Chapter]):
        logger.info(lang["main"]["retry_st"])
        retry = self.ser.asyncDownload(chaps)  # type: ignore
        cnt = 0
        max_task = MAX_TASK
        while len(retry):
            logger.info(lang["main"]["retry_st"])
            sleep(WAIT_TIME)
            max_task //= RETRY_SUB
            if max_task < 1:
                max_task = 1
            logger.info(lang["main"]["retry_st"])
            retry = self.ser.asyncDownload(list(retry), int(max_task))
            cnt += 1
            if cnt > MAX_RETRY and len(retry) > 0:
                logger.error(lang["main"]["fail1"])
                logger.error(lang["main"]["fail2"])
                logger.error(retry)
                for chap in retry:
                    copy("fail.mp3", self.optDir + "/" + chap.title)
                return retry
        logger.info(lang["main"]["tts_end"])

    def merge(self, chaps: list[Chapter]):
        logger.info(lang["main"]["mer_st"])
        merge(chaps, self.optDir, True)
        logger.info(lang["main"]["mer_end"])

    def __call__(self):
        book, area = self.interactive()
        chaps = self.dealApp(book, area)
        chaps = self.textTrans(chaps)
        # print(chaps[0].content)
        retry = self.tts(chaps)
        self.merge(chaps)
        if retry is not None:
            retry = set(retry)
            logger.info(
                lang["main"]["all_failed"] +
                " ".join([str(i.idx) for i in retry])
            )
            k = len(retry) / len(chaps)
            if k > 0.7:
                logger.info(lang["main"]["too_many_failed_1"])
                logger.info(lang["main"]["too_many_failed_2"] % k * 100)
                logger.info(lang["main"]["too_many_failed_3"])
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
        t = time_fmt(end - bgn)
        logger.info(lang["main"]["end_1"] + t)
        logger.info(lang["main"]["end_2"] % ((end - bgn) / length))
        logger.info(lang["main"]["end_3"] %
                    ((main.ser.total_time * 60 / (end - bgn))))

    except SystemExit as e:
        logger.info(
            f"SystemExit with code {e.code} got, may exit not normally.")
        return
    except KeyboardInterrupt:
        logger.info("Got keyboard interrupt, exit forcely.")
        return
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)()


if __name__ == "__main__":
    main(TRANS_MODE)
    input("Press enter to exit.")
