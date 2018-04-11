import requests
import urllib.parse
from bs4 import BeautifulSoup as bs
import binascii
from ctypes import *
import re

mydll = cdll.LoadLibrary('LyricDecoder.dll')
mydll.qrcdecode.restype=c_char_p

extract_xml_re=re.compile(r'<Lyric_1 LyricType="1" LyricContent="(.*?)"/>',re.DOTALL)

def qrc_decode(data):
    return mydll.qrcdecode(data,len(data))
    
def query_lyric(name,singer):
    res=requests.get('https://c.y.qq.com/lyric/fcgi-bin/fcg_search_pc_lrc.fcg',params=dict(
        SONGNAME=name,
        SINGERNAME=singer,
        TYPE=2,
        RANGE_MIN=1,
        RANGE_MAX=20,
    ))
    res.raise_for_status()
    soup=bs(res.text,'xml')
    for song in soup.find_all('songinfo'):
        yield dict(
            songid=song['id'],
            name=urllib.parse.unquote(song.find('name').text),
            singer=urllib.parse.unquote(song.find('singername').text),
            album=urllib.parse.unquote(song.find('albumname').text),
        )
        
def download_lyric(songid):
    res=requests.get('https://c.y.qq.com/qqmusic/fcgi-bin/lyric_download.fcg',params=dict(
        version='15',
        miniversion='82',
        lrctype='4',
        musicid=songid,
    ))
    res.raise_for_status()
    soup=bs(res.text.replace('<!--','').replace('-->',''),'xml')
    
    def decode(obj):
        return binascii.unhexlify(obj.text.encode('ascii'))
    
    return dict(
        orig=decode(soup.find('content')),
        ts=decode(soup.find('contentts')),
        roma=decode(soup.find('contentroma')),
    )
    
def tamper_lyric(data):
    return b'[offset:0]\n'+data
    
def extract_xml(data):
    if '<?xml ' not in data[:10]:
        #return ''
        return data
    #so that `\n`s are preversed
    return extract_xml_re.search(data).groups()[0]
    
def fetch_lyric_by_id(songid,requested_type):
    lrc=download_lyric(songid)
    ret={}
    for typ in requested_type:
        ret[typ]=extract_xml(qrc_decode(tamper_lyric(lrc[typ])).decode('utf-8','ignore'))
    return ret
    
#print(list(query_lyric('ユキトキ','やなぎなぎ')))
#lrc=download_lyric(4804827)
#with open('roma.xml','wb') as f:
#    f.write(qrc_decode(tamper_lyric(lrc['roma'])))
#with open('orig.xml','wb') as f:
#    f.write(qrc_decode(tamper_lyric(lrc['orig'])))
#with open('ts.xml','wb') as f:
#    f.write(qrc_decode(tamper_lyric(lrc['ts'])))

if __name__=='__main__':
    title=input('Title: ')
    artist=input('Artist: ')
    print('Searching...')
    songlist=list(query_lyric(title,artist))
    for ind,song in enumerate(songlist):
        print('#%d: %s / %s / %s'%(ind,song['name'],song['singer'],song['album']))
    cid=int(input('Select #: '))
    songid=songlist[cid]['songid']
    print('Song ID = %s'%songid)
    print('Downloading...')
    res=fetch_lyric_by_id(songid,['orig','ts','roma'])
    for typ,data in res.items():
        print('=== Showing: %s'%typ)
        print(data)