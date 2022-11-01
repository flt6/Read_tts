from json import load
from os import listdir
from re import search

def main(file:str):
    with open(file,"r",encoding="utf-8") as f:
        lang = load(f)

    dir = listdir()
    suc = True

    for file in dir:
        if ".py" not in file:
            continue
        with open(file,"r",encoding="utf-8") as f:
            lines = f.readlines()
            for line in lines:
                t=search(r"lang\[.+\]",line)
                if t is not None:
                    try:
                        exec(t.group())
                    except KeyError as e:
                        suc = False
                        print("Key '%s' not found!"%(e.args[0],))
    return suc

if __name__ == "__main__":
    print("ATTENTION: This script is not safe! Please only try on known file.")
    file=input("`lang.json` filename(including extension): ")
    if main(file):
        print("Success.")
    else:
        print("The following keys is not available.")
        print("Please add these keys.")