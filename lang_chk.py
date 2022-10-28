from json import load
from os import listdir
from re import search

with open("lang_en_d.json","r",encoding="utf-8") as f:
    lang = load(f)

dir = listdir()

for file in dir:
    if ".py" in file:
        with open(file,"r",encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                t=search(r"lang\[.+\]",line)
                if t is not None:
                    print(t.group())
                    exec(t.group())