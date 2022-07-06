中文 | [ENGLISH](https://github.com/MC-dusk/QRCD_M/blob/master/README_EN.md)

# [QRCD_M](https://github.com/MC-dusk/QRCD_M)

修改自`QRCD`，自用。去除了原QRCD的网页GUI和播放歌词的功能（因为[用不了](https://github.com/xmcp/QRCD/issues/2)），只留下下载歌词的功能。

白嫖QQ音乐的打轴，只需输入歌曲名即可得到精准逐字lrc歌词，再也不用K轴辣！

## 使用

1. 安装python
2. 下载[代码库zip包](https://github.com/MC-dusk/QRCD/archive/refs/heads/master.zip)
3. 在解压出的文件夹路径下打开命令行输入`pip install requirements.txt`
4. 若无报错，双击`qrcd_m.py`运行（当然也可在命令行里运行）
5. 输入歌曲名（留空即退出），歌手名（可留空），根据返回序号选择其中一个下载（一般ID越大歌词越新）
6. 下载结果在lyric子文件夹中，3个逐行的lrc，2个逐字的lrc，ignore是一些忽略的前置信息

## 用途

- 在[foobar2000](https://www.foobar2000.org/)播放器中使用。
- 使用[lua插件](https://github.com/qwe7989199/Lyric-Importer-for-Aegisub)将lrc导入aegisub中，进而制作歌词字幕或其他用途。

# [QRCD](https://github.com/xmcp/QRCD)

> Fork自[QRCD](https://github.com/xmcp/QRCD)，以下是QRCD的简介。

一个从QQMusic爬取歌词的python脚本。

使用QQ音乐的PC客户端的API，和网页API相比，额外支持了精准逐字lrc歌词（即KTV/卡拉OK歌词）和罗马音歌词（日语歌曲）。

*Note: decrypting algorithm learnt from [qwe7989199/Lyric-Importer-for-Aegisub](https://github.com/qwe7989199/Lyric-Importer-for-Aegisub).*

