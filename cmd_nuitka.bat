python -m nuitka --follow-imports --noinclude-IPython-mode=nofollow --standalone  --include-data-file=fail.mp3=. --assume-yes-for-downloads --onefile  --mingw64 --lto=yes --nofollow-import-to=pydoc --nofollow-import-to=multiprocessing interactive/console.py
python -m nuitka --follow-imports --noinclude-IPython-mode=nofollow --include-data-file=fail.mp3=. --assume-yes-for-downloads --onefile  --mingw64 --lto=yes --nofollow-import-to=pydoc --nofollow-import-to=multiprocessing --show-progress --noinclude-IPython-mode=nofollow --standalone --include-data-file="server\fail.mp3"=fail.mp3 --include-data-file="server\7z.dll"=7z.dll --include-data-file="server\7za.exe"=7za.exe --onefile server\server.py
pause
 