from log import getLogger
from consts import MAX_RETRY, OPT_DIR
from utils import ToApp
from exceptions import ErrorHandler
from traceback import format_exc
from pickle import dump


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
        return chaps, to-bgn+1

    def __call__(self, type: int, optDir: str):
        chaps = self.dealApp()
        with open("chap.dmp", "wb") as f:
            dump((chaps, optDir, type), f)


if __name__ == '__main__':
    try:
        main = Main()
        main(1, OPT_DIR)
    except BaseException as e:
        logger.critical("Uncaught exception")
        logger.critical(format_exc())
        ErrorHandler(e, "UNCAUGHT", logger, 3, True, True)
