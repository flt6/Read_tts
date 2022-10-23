from azure.cognitiveservices.speech import ResultReason  # type: ignore

SSML_MODEL = '''<speak xmlns="http://www.w3.org/2001/10/synthesis" xmlns:mstts="http://www.w3.org/2001/mstts" xmlns:emo="http://www.w3.org/2009/10/emotionml" version="1.0" xml:lang="en-US">
    <voice name="zh-CN-YunyeNeural">
        <prosody rate="43%" pitch="0%">
            {}
        </prosody>
    </voice>
</speak>'''

GET_SHELF = "http://{}/getBookshelf"
GET_CHAPTER_LIST = "http://{}/getChapterList?url={}"
GET_CONTENT = "http://{}/getBookContent?url={}&index={}"

MODE_CHOOSE = '''\
Choose running mode:
1. Basic
2. Fix
3. Concat
4. Delete temporary files
'''

CHOOSEBOOK = '''
No.     %02d
name:   %s
author: %s
now:    %s
-----------------
'''


DEFAULT_CONFIG={
    'MAX_RETRY' : 5,
    'MAX_TASK'  : 10,
    'MAX_CHAR'  : 1500,
    "WAIT_TIME" : 5,
    "RETRY_SUB" : 2,
    "LIMIT_429" : 0.7,
    "MAX_WAIT"  : 20,
    "FAIL_429"  : 3,
    "TIMEOUT"   : 3,
    'OPT_DIR'   : "Output",
    'DEBUG'     : False,
    'TO_CONSOLE': True
}

DEFAULT_TYPE={
    'MAX_RETRY' : (int,),
    'MAX_TASK'  : (int,),
    'MAX_CHAR'  : (int,),
    "WAIT_TIME" : (int,float),
    "RETRY_SUB" : (int,float),
    "LIMIT_429" : (float,),
    "MAX_WAIT"  : (int,),
    "FAIL_429"  : (int,),
    "TIMEOUT"   : (int,float),
    'OPT_DIR'   : (str,),
    'DEBUG'     : (bool,),
    'TO_CONSOLE': (bool,)
}

lang=[
    "书籍无效",
    "无法读取当前进度",
    "章节(例如: '1 2 3'): ",
    "输入数据不满足正则表达式检测要求",
    "HTTP连接 状态码：%d",
    "无法连接到服务器",
    "无法连接到APP",
    "存在'ip.conf'文件",
    "请先删除对应文件夹, 否则IP不能保存",
    "存在ip.conf文件夹",
    "成功初始化连接APP模块",
    "429: UPS限制",
    "原因: ",
    "音频时长为0，而且不是因为429限制",
    "需要重试 %02d 个| 成功率: %0.2f%%",
    "交互主程序初始化成功",
    "运行模式无效",
    "正在获取书架",
    "无效`typ`：%d",
    "开始获取章节",
    "开始（新一轮）的重试",
    "在反复重试后仍无法获取书架",
    "获取章节失败列表",
    "成功从app处获取数据",
    "开始进行音频下载",
    "开始等待重试",
    "开始（新一轮）的重试",
    "在反复重试后仍无法获取书架",
    "获取章节失败列表"
]

TTS_SUC = ResultReason.SynthesizingAudioCompleted
TTS_CANCEL = ResultReason.Canceled
