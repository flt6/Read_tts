from utils import Trans
from model import Chapter
from rich import print

trans = Trans(2)
chap = Chapter(1,"Titile","1'23'45\nAE\"88\"sd“f”jl")

# print(trans._chk(chap.content))
# print(trans.area)
print(trans.__call__(chap))