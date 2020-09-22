# QRCD

A python tool to crawl & decrypt lyrics from QQMusic.

It uses the API for QQMusic PC client, so **romanized lyrics & real-time (KTV) lyrics are supported**, unlike other WebAPI-based tools.

*Note: decrypting algorithm learnt from [qwe7989199/Lyric-Importer-for-Aegisub](https://github.com/qwe7989199/Lyric-Importer-for-Aegisub).*

## displayer

A simple lyric viewer with romanization support.

![image](https://user-images.githubusercontent.com/6646473/93913756-1aeda800-fd38-11ea-940c-afd68d9fe298.png)

**Usage:**

Go to `http://127.0.0.1/` for control window.

Search by song title & singer name.

Click on `Open Player` to open popup window for current search result. (Note that popup window shows nothing upon initialization. Press <kbd>D</kbd> to activate it.)

**Keyboard controlling: (both control window and popup window)**

- <kbd>P</kbd> Play/Pause
- <kbd>[</kbd> <kbd>]</kbd> Seek ±1s
- <kbd>-</kbd> <kbd>=</kbd> Seek ±150ms
- <kbd>J</kbd> <kbd>K</kbd> Seek ±1line
- <kbd>0</kbd> Pause at beginning
- <kbd>R</kbd> Toggle romanization
- <kbd>T</kbd> Toggle translation
- <kbd>H</kbd> Toggle highlighting
- <kbd>D</kbd> Toggle global display (and pause)
- <kbd>S</kbd> Change song by ID

**Mouse controlling: (both control window and popup window)**

- <kbd>Ctrl</kbd>+Click to pause at selection