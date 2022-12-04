from utils import Trans, Queue, quote
from model import Chapter
from rich import print

print(quote("\x01\x02"))
trans = Trans(2)
chap = Chapter(1,"Titile","1'23'45\nAE\"88\"sd“f”jl")

# # print(trans._chk(chap.content))
# # print(trans.area)
print(trans.__call__(chap)[0].content)

# que = Queue()
# que.push((1,1))
# que.push((1,1))
# que.push((2,3))
# que.push((4,5))

# print(que)