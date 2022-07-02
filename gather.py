from requests import get
from json import loads
from traceback import format_exc
from log import Log
import re
from os import path,mkdir,system
from tts import mainSeq,getLogger
import asyncio
from alive_progress import alive_bar
from sys import exit


DEBUG = None

USE_CHAC = False
# 如果单章节有50句以上角色句子（一组上下引号为一句）, 请禁用此功能。
# 如果文章不能做到上下引号严格配对（包括“..."），请禁用此功能

SSML_MODEL = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-XiaoxiaoNeural">
        <prosody rate="45%" pitch="0%">
            {}
        </prosody>
    </voice>
</speak>'''
if DEBUG is None:
    DEBUG=path.exists("DEBUG")
logger = Log("Main",debug=DEBUG,show=True).get_logger()
getLogger(True,DEBUG)


class Main:
    def __init__(self, ip:str, use_chac:bool) -> None:
        '''
            Func: init
            Parm: 
                ip:       ip to app
                use_chac: use diffterent voice for chacrater sentence.
                NOTICE:   如果单章节有50句以上角色句子（一组上下引号为一句）, 请禁用此功能。
                          如果文章不能做到上下引号严格配对（包括“..."），请禁用此功能
        '''
        self.books = []
        self.retry = []
        self.ip = ip
        self.use_chac = use_chac
        self.tasks = []
        self.text = []
        self.l = []
        if not path.isdir("read"):
            if path.exists("read"):
                logger.critical("Exists File named 'read', which should be a dictionary for save.")
                exit(2)
            mkdir("read")
        if use_chac:
            logger.warning("USE_CHAC function is ON, please check if your book is supported.")

    def get_shelf(self) -> bool:
        '''
            Func:   Get Shelf
            return: Is succeeded
        '''
        try:
            shelf = loads(
                get("http://{}/getBookshelf".format(self.ip)).text)["data"]
        except KeyboardInterrupt as e:
            raise e
        except Exception:
            logger.critical(f"Can't Get Shelf from {self.ip}")
            logger.debug(format_exc())
            ip = input("ip: ")
            if ":" not in ip:
                ip += ":1122"
            with open("ip.conf","w") as f:
                f.write(ip)
            self.get_shelf()
        for i in range(len(shelf)):
            if shelf[i]["durChapterIndex"] == 0:
                continue
            self.books.append({
                "name": shelf[i]["name"],
                "author": shelf[i]["author"],
                "now": shelf[i]["durChapterTitle"],
                "now_idx": shelf[i]["durChapterIndex"],
                "totalChapterNum": shelf[i]["totalChapterNum"],
                "url": shelf[i]["bookUrl"]
            })
            print("No.%02d\n\tname:%s\n\tauthor:%s\n\tnow:%s\n-------------" %
                  (i+1, shelf[i]["name"], shelf[i]["author"], shelf[i]["durChapterTitle"]))
        return True

    def choose_book(self) -> None:
        self.num = int(input("No. "))-1
        self.bgn = input("From(%d: %s): " % (
            self.books[self.num]["now_idx"], self.books[self.num]["now"]))
        if self.bgn == "":
            self.bgn = self.books[self.num]["now_idx"]
        else:
            self.bgn  =  int(self.bgn)
        self.to = int(input(("To. ")))
        self.data = self.books[self.num]
        logger.debug(f"bgn: {self.bgn} to: {self.to}")

    def get_charpter_list(self) -> list:
        url = "http://{}/getChapterList".format(self.ip)
        l = loads(get(url, params={"url": self.data["url"]}).text)["data"]
        return l

    def _download(self,f,name=None) -> asyncio.Task:
        task=asyncio.create_task(f)
        task.set_name(name)
        return task

    async def wait(self,bgn,is_retry,bar):
        # self.
        for id,i in enumerate(self.tasks):
            i:asyncio.Task
            try:
                await i
            except KeyboardInterrupt as e:
                raise e
            except:
                if i.exception() is not None:
                    if not is_retry:
                        try:
                            logger.error(
                                "ERROR: Get %d %s Error, added to retry list." % (bgn+id, i.get_name()))
                            logger.debug(i.exception())
                            logger.debug(f"bgn: {bgn}, id:{id}")
                            self.retry.append(self.text[bgn+id])
                        except Exception:
                            logger.exception("Add retry list error.")
                    else:
                        try:
                            logger.error(
                                "ERROR: Get %d %s Error WHILE RETEYING" % (bgn+id, i.get_name()))
                            logger.error(i.exception())
                            logger.debug(f"bgn: {bgn}, id:{id}")
                        except Exception:
                            logger.exception("RETRY Error.")
            bar()

    def download_content(self,l,is_retry) -> None:
        iter = range(self.bgn, self.to+1) if not is_retry else self.retry
        print("Getting contents...")
        with alive_bar(len(iter)) as bar:
            for i in iter:
                url = "http://{}/getBookContent".format(self.ip)
                title = l[i]["title"]
                title = re.sub(r'''[\*\/\\\|\<\>\? \:\.\'\"\!]''',"",title)
                try:
                    cha = loads(get(url, params={"url": self.data["url"], "index": str(i)}).text)[
                        "data"]
                except KeyboardInterrupt as e:
                    raise e
                except Exception:
                    if not is_retry:
                        logger.error(
                            "ERROR: Get %d %s from app Error, added to retry list." % (i, title))
                        logger.debug(format_exc())
                        self.retry.append(i)
                    else:
                        logger.error(
                            "ERROR: Get %d %s from app Error WHILE RETEYING" % (i, title),
                            exc_info=True
                        )
                    continue
                SSML_text = SSML_MODEL.format(cha)
                if self.use_chac:
                    SSML_text = re.sub(
                        "“|【", "</prosody></voice><voice name=\"zh-CN-XiaomoNeural\"><prosody rate=\"45%\" pitch=\"0%\">“", SSML_text)
                    SSML_text = re.sub(
                        "”|】", "</prosody></voice><voice name=\"zh-CN-XiaoXiaoNeural\"><prosody rate=\"45%\" pitch=\"0%\">", SSML_text)
                output_path = "read/%s" % (title)
                logger.debug("Get %03d %s" % (i, title))
                bar()
                try:
                    self.text.append(((SSML_text,output_path),title))
                except:
                    logger.error("Error while adding task to list.")
                    logger.debug("DBG",exc_info=True)
        # reset to the begin
        get(url, params={"url": self.data["url"], "index": str(self.bgn)})

    async def download(self, l, is_retry=False) -> None:
        iter=self.retry if is_retry else self.text
        logger.debug([tmp[1] for tmp in self.retry])
        with alive_bar(len(self.text)+1) as bar:
            for id,((SSML_text,output_path),name) in enumerate(iter):
                self.tasks.append(
                    self._download(mainSeq(SSML_text, output_path),name)
                )
                logger.debug(f"Created task: id={id},name={name}")
                if id % 5 == 0 and id != 0:
                    logger.info(f"waiting for group {id//5}(from {id-5} to {id})")
                    await self.wait(id-5,is_retry,bar)
                    self.tasks = []
            logger.info(f"waiting for last group.")
            logger.error("TODO: last group.")
            await self.wait(-1,is_retry,bar)
            bar()
            self.tasks = []

    def main(self):
        if not self.get_shelf():
            return 1
        self.choose_book()
        l = self.get_charpter_list()
        self.download_content(l,False)
        if len(self.retry) != 0:
            logger.info("Begin to retry downloading text.")
            self.download_content(l,True)
            self.retry=[]
        logger.info("Begin to download audios.")
        asyncio.run(self.download(l,False))
        if len(self.retry) == 0:
            logger.info("Succeeded")
            return 0
        logger.info("Begin to retry.")
        asyncio.run(self.download(l,True))
        return 0


if __name__ == '__main__':
    if path.exists("ip.conf"):
        with open("ip.conf","r") as f:
            ip = f.read()
    else:
        ip = input("ip: ")
        if ":" not in ip:
            ip += ":1122"
        with open("ip.conf","w") as f:
            f.write(ip)
    main = Main(ip,USE_CHAC)
    try:
        ret=main.main()
        if ret != 0:
            logger.error(f"main.mian() returned {ret}")
    except SystemExit:
        exit()
    except KeyboardInterrupt:
        logger.error("Keyboard Interrupt")
        exit()
    except ConnectionResetError:
        logger.critical("网络错误，请重试。")
        logger.debug("ConnectionResetError caught in main",exc_info=True)
    except Exception:
        logger.critical("An uncaught error occurred during Main.main",exc_info=True)
        system("pause")