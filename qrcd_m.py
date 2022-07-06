from os import mkdir
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup as bs
import binascii
import subprocess
import re
import datetime
import zlib

def qrc_decode(data):
    data=binascii.hexlify(data)
    p=subprocess.Popen('lib_qrc_decoder.exe',stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate(data+b'\n\n')
    if stderr:
        raise RuntimeError(stderr.decode(errors='ignore'))
    data=binascii.unhexlify(stdout.strip())
    try:
        return zlib.decompress(data)
    except Exception as e:
        print('!! decode error',type(e),e)
        return b''
    
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
        txt=obj.text
        if txt.strip():
            return binascii.unhexlify(txt.encode('ascii'))
        else:
            return b''
    
    return dict(
        orig=decode(soup.find('content')),
        ts=decode(soup.find('contentts')),
        roma=decode(soup.find('contentroma')),
    )
    
def tamper_lyric(data):
    return b'[offset:0]\n'+data
    
def lrc_to_dummy_qrc(data):
    lrc_line_re=re.compile(r'^\[(\d+:\d+(?:\.\d+)?)\](.*)$')
    outputs=[]
    for line_s in data.replace('\r','').split('\n'):
        line=lrc_line_re.match(line_s)
        if not line:
            # print('ignored LINE:',line_s)
            continue
            
        timestamp,content=line.groups()
        time=datetime.datetime.strptime(timestamp,'%M:%S.%f')
        
        outputs.append((time.minute*60*1000+time.second*1000+time.microsecond//1000,content))
        
    if not outputs:
        return ''
    
    outputs.append((2147483647,'')) # end
    
    return '\n'.join([
        '[%d,%d]%s'%(time,outputs[ind+1][0]-time,content) for ind,(time,content) in enumerate(outputs[:-1]) if content
    ])
    
def extract_qrc_xml(data):
    extract_xml_re=re.compile(r'<Lyric_1 LyricType="1" LyricContent="(.*?)"/>',re.DOTALL)
    if '<?xml ' not in data[:10]:
        #return data
        return lrc_to_dummy_qrc(data)
    #so that `\n`s are preversed
    return extract_xml_re.search(data).groups()[0]
    
def fetch_lyric_by_id(songid,requested_type):
    lrc=download_lyric(songid)
    ret={}
    for typ in requested_type:
        if lrc[typ]:
            ret[typ]=extract_qrc_xml(qrc_decode(lrc[typ]).decode('utf-8','ignore'))
        else:
            ret[typ]=''
    return ret
    # return lrc

def down_lyric_line(songid):
    for lrc_type in ['orig','roma','ts']:
        lrc=fetch_lyric_by_id(songid,['orig','roma','ts'])[lrc_type]
        
        line_re=re.compile(r'^\[(\d+),\d+\](.*)$')
        repl_re=re.compile(r'\(\d+,\d+\)')
        
        lrc_out=''
        line_ign=''
        
        def format_time(ts):
            # # 时间戳，三位小数兼容性不足，换用两位小数
            # return f'{ts//60000:02d}:{(ts//1000)%60:02d}.{ts%1000:03d}'
            return f'{ts//60000:02}:{(ts//1000)%60:02}.{ts%1000//10:02}'

        for line in lrc.splitlines():
            line_res=line_re.match(line)
            if not line_res:
                # print('ignoring line',line)
                line_ign+=line+'\n'
                continue
            start_ts,line_out=line_res.groups()
            line_out=repl_re.sub('',line_out)
            lrc_out+=f'[{format_time(int(start_ts))}]{line_out}\n'

            lrc_output(lrc_type,line_ign,lrc_out,'line')

def down_lyric_syl(songid):
    for lrc_type in ['orig','roma']:
        lrc=fetch_lyric_by_id(songid,['orig','roma'])[lrc_type]
        
        line_re=re.compile(r'^\[(\d+),(\d+)\](.*)$')
        syl_re=re.compile(r'(.+?)\((\d+),\d+\)')
        
        lrc_out=''
        line_ign=''
        
        def format_time(ts):
            # 时间戳小数部分，从向下取整变为四舍五入
            ts=round(ts/10)*10
            return f'{ts//60000:02}:{(ts//1000)%60:02}.{ts%1000//10:02}'
        
        for line in lrc.splitlines():
            line_res=line_re.match(line)
            if not line_res:
                # print('ignoring line',line)
                line_ign+=line+'\n'
                continue
            line_start,line_dur,line_lyric=line_res.groups()
            syl_list=syl_re.finditer(line_lyric)
            line_out=''
            for syl in syl_list:
                char,syl_start=syl.groups()
                line_out+=f'[{format_time(int(syl_start))}]{char}'
            line_out+=f'[{format_time(int(line_start)+int(line_dur))}]'
            lrc_out+=f'{line_out}\n'

            lrc_output(lrc_type,line_ign,lrc_out,'syl')

def lrc_output(lrc_type,line_ign,lrc_out,type):
        f=open(f'lyric/{title}_{lrc_type}_{type}_ignore_{unix_time}.txt', mode='w', encoding='utf-8')
        f.write(line_ign)
        f.close()

        f=open(f'lyric/{title}_{lrc_type}_{type}_{unix_time}.lrc', mode='w', encoding='utf-8')
        f.write(lrc_out)
        f.close()    

def main():
    global title
    title=input('Input nothing to exit...\nTitle: ')
    if title=='':
        quit()
    artist=input('Artist: ')
    print('Searching...')
    songlist=list(query_lyric(title,artist))
    for ind,song in enumerate(songlist):
        print('#%d: (%s) %s / %s / %s'%(ind,song['songid'],song['name'],song['singer'],song['album']))
    cid=int(input('Select #: '))
    songid=songlist[cid]['songid']
    print('Song ID = %s'%songid)
    print('Downloading...')
    try:
        mkdir('./lyric')
    except:
        pass

    # # output original decode text
    # res=fetch_lyric_by_id(songid,['orig','ts','roma'])
    # for typ,data in res.items():
    #     f=open('lyric/'+typ+'_decode.lrc', mode='w', encoding='utf-8')
    #     f.write(data)
    #     f.close()

    # 加入unix时间戳防止输出被重复覆盖
    global unix_time
    unix_time = str(int(time.time()))
    down_lyric_line(songid)
    down_lyric_syl(songid)
    print('Success, next song waiting...')

if __name__=='__main__':
    while 1:
        main()
