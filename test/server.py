from fastapi import FastAPI
# from uvicorn import run

shelf = '{"data":[{"author":"作者","bookUrl":"https://m.***.com/*ab*.html","canUpdate":true,"coverUrl":"https://***/972184.jpg","customCoverUrl":"https://***/***/300","durChapterIndex":512,"durChapterPos":789,"durChapterTime":1664591099022,"durChapterTitle":"latestChapterTitle","group":0,"intro":"introduce","kind":"kind","lastCheckCount":0,"lastCheckTime":1664459085609,"latestChapterTime":1664459085609,"latestChapterTitle":"最后","name":"名称","order":-31,"origin":"https://***.com","originName":"源名称","originOrder":-88903130,"readConfig":{"delTag":0,"imageStyle":"0","reSegment":false,"reverseToc":false,"splitLongChapter":true,"useReplaceRule":true},"tocUrl":"https://m.***.com/804280/","totalChapterNum":695,"type":0,"wordCount":"字数"}],"errorMsg":"","isSuccess":true}'
chaplist = '{"data":[{"baseUrl":"https://***/***/","bookUrl":"https://m.***.com/*ab*.html","index":0,"isPay":false,"isVip":false,"isVolume":false,"tag":"","title":"title  1","url":"/***/****.html"},{"baseUrl":"https://***/***/","bookUrl":"https://m.***.com/*ab*.html","index":1,"isPay":false,"isVip":false,"isVolume":false,"tag":"","title":"title  2","url":"/***/****.html"},{"baseUrl":"https://***/***/","bookUrl":"https://m.***.com/*ab*.html","index":2,"isPay":false,"isVip":false,"isVolume":false,"tag":"","title":"title  3","url":"/***/****.html"}],"errorMsg":"","isSuccess":true}'
text = '{"data":"test chapter texts, page number is {}","errorMsg":"","isSuccess":true}'

app = FastAPI()


@app.get("/getBookshelf")
def getshelf():
    return shelf


@app.get("/getChapterList")
def getchap(url: str):
    assert url == "https://m.***.com/*ab*.html"
    return chaplist


@app.get("/getBookContent")
def getcon(url: str, index: int):
    assert url == "https://m.***.com/*ab*.html"
    return text.format(index)
