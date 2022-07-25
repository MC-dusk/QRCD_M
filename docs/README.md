> **中文 | [ENGLISH](https://github.com/MC-dusk/QRCD_M/blob/master/docs/README_EN.md)**

# [QRCD_M](https://github.com/MC-dusk/QRCD_M)

修改自`QRCD`，自用。去除了原QRCD的网页GUI和播放歌词的功能（因为[用不了](https://github.com/xmcp/QRCD/issues/2)），只留下下载歌词的功能。

> 白嫖QQ音乐的打轴，只需输入歌曲名即可得到精准逐字lrc歌词，再也不用K轴辣！

## 使用

### 首选

1. 下载[release](https://github.com/MC-dusk/QRCD_M/releases)解压，运行`qrcd_m.exe`直接使用。（[v1.0备份](https://wwi.lanzoup.com/iIojh07ka10j)）
2. 输入歌曲名（留空即退出），歌手名（可留空），根据返回序号选择其中一个下载（一般ID越大歌词越新）。
3. 下载结果在lyric子文件夹中，按歌曲名分类。根据歌曲语言，最多有3个逐行的lrc，2个逐字的lrc，1个双语逐字歌词。ignr是一些忽略的前置信息，如不需要可手动删除。

### 可选

新功能会先更新到bin文件夹中的py文件，如果本地安装了python，也可以直接运行py文件，但您仍然需要在同一路径下放置`lib_qrc_decoder.exe`、`QQMusicCommon.dll`，如果提示缺少运行库还需要放置`msvcp100.dll`、`msvcr100.dll`。

1. 下载[zip包](https://github.com/MC-dusk/QRCD_M/archive/refs/heads/master.zip)并解压。
2. 执行`pip install -r requirements.txt`。
2. 运行`qrcd_m.py`。

## 用途

- 在[foobar2000](https://www.foobar2000.org/)播放器中使用。
- 使用[lua插件](https://github.com/qwe7989199/Lyric-Importer-for-Aegisub)将lrc导入aegisub中，进而制作歌词字幕或其他用途。

# [QRCD](https://github.com/xmcp/QRCD)

> Fork自QRCD，以下是原简介（翻译后）。

一个从QQMusic爬取歌词的python脚本。

使用QQ音乐的PC客户端的API，和网页API相比，额外支持了精准逐字lrc歌词（即KTV/卡拉OK歌词）和罗马音歌词（日语歌曲）。

*注：解密算法来自[qwe7989199/Lyric-Importer-for-Aegisub](https://github.com/qwe7989199/Lyric-Importer-for-Aegisub).*

[![Page Views Count](https://badges.toozhao.com/badges/01G6ZJY3322Y59H9X1J3XHN2M5/green.svg)](https://badges.toozhao.com/stats/01G6ZJY3322Y59H9X1J3XHN2M5 "Get your own page views count badge on badges.toozhao.com")

