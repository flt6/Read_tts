python -m nuitka --follow-imports --noinclude-IPython-mode=nofollow --standalone  --include-data-file=fail.mp3=. --assume-yes-for-downloads --onefile  --mingw64 --lto=yes --nofollow-import-to=pydoc --nofollow-import-to=multiprocessing main.py
pause
 