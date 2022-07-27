import os
import sys
import time
import requests
import urllib.parse
from bs4 import BeautifulSoup as bs
import binascii
import subprocess
import re
import datetime
import zlib

if getattr(sys, 'frozen', False):
    root_path = os.path.dirname(sys.executable)
else:
    root_path = os.path.dirname(__file__)

def qrc_decode(data):
    data=binascii.hexlify(data)
    p=subprocess.Popen(root_path+'/lib_qrc_decoder.exe',stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    stdout,stderr=p.communicate(data+b'\n\n')
    if stderr:
        raise RuntimeError(stderr.decode(errors='ignore'))
    data=binascii.unhexlify(stdout.strip())

    # # test code
    # f=open(root_path+f'/lyric/data.txt', mode='wb')
    # f.write(data)
    # f.close()

    try:
        return zlib.decompress(data, zlib.MAX_WBITS|32)
    except Exception as e:
        print('! decode error',type(e),e,'!')
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
    
    outputs.append((2147483647,'')) # end # 2147483647 = 2^31 - 1
    
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
    # # 返回未解密歌词
    # return lrc
    ret={}
    for typ in requested_type:
        if lrc[typ]:
            ret[typ]=extract_qrc_xml(qrc_decode(lrc[typ]).decode('utf-8','ignore'))
        else:
            ret[typ]=''
    return ret

def down_lyric_line(res):
    for language_type in ['orig','roma','ts']:
        lrc=res[language_type]
        
        line_re=re.compile(r'^\[(\d+),\d+\](.*)$')
        repl_re=re.compile(r'\(\d+,\d+\)')

        lrc_out=''
        line_ign=''

        for line in lrc.splitlines():
            line_res=line_re.match(line)
            if not line_res:
                # print('ignoring line',line)
                line_ign+=line+'\n'
                continue
            start_ts,line_out=line_res.groups()
            line_out=repl_re.sub('',line_out)
            lrc_out+=f'[{format_time(int(start_ts))}]{line_out}\n'
        
        if lrc_out == '':
            continue
        lrc_output(language_type,line_ign,lrc_out,'line')

def down_lyric_char(res):
    for language_type in ['orig','roma']:
        lrc=res[language_type]
        
        line_re=re.compile(r'^\[(\d+),(\d+)\](.*)$')
        char_re=re.compile(r'(.+?)\((\d+),\d+\)')
        
        lrc_out=''
        line_ign=''

        for line in lrc.splitlines():
            line_res=line_re.match(line)
            if not line_res:
                # print('ignoring line',line)
                line_ign+=line+'\n'
                continue
            line_start,line_dur,line_lyric=line_res.groups()
            char_list=char_re.finditer(line_lyric)
            line_out=''
            for char in char_list:
                char,char_start=char.groups()
                line_out+=f'[{format_time(int(char_start))}]{char}'
            line_out+=f'[{format_time(int(line_start)+int(line_dur))}]'
            lrc_out+=f'{line_out}\n'
        
        if lrc_out == '':
            continue
        lrc_output(language_type,line_ign,lrc_out,'char')

def down_lyric_mix(res):
        lrc_og=res['orig']
        lrc_ch=res['ts']
        if lrc_og == '':
            print('! No original lyric !')
            return 1
        if lrc_ch == '':
            print('* No translated lyric')
            return 0
        
        line_re=re.compile(r'^\[(\d+),(\d+)\](.*)$')
        char_re=re.compile(r'(.+?)\((\d+),\d+\)')
        repl_re=re.compile(r'\(\d+,\d+\)')
        
        lrc_out=''
        line_ign=''
        
        list_og=lrc_og.splitlines()
        list_ch=lrc_ch.splitlines()

        len_og = len(list_og)
        # "line_df" is the amount of lines which can't be paired between "og" and "ch"
        for line_df in range(len_og):
            line_og=list_og[line_df]
            line_og_res=line_re.match(line_og)
            if not line_og_res==None:
                break
            line_ign+=line_og+'\n'
        if len_og != (len(list_ch) + line_df):
            # print(len_og, len(list_ch), line_df)
            print("! Can't mix two languages for different amount of line !")
            return

        for i in range(len_og-line_df):
            line_og=list_og[i+line_df]
            line_og_res=line_re.match(line_og)
            line_ch=list_ch[i]
            line_ch_res=line_re.match(line_ch)

            # # 歌词中间的行一般不会有问题，注释掉节省判断
            # if not line_og_res:
            #     line_ign+=line_og+'\n'
            # if not line_ch_res:
            #     line_ign+=line_ch+'\n'
            # if not (line_og_res and line_ch_res):
            #     continue

            line_start,line_dur,line_lyric=line_og_res.groups()
            char_list=char_re.finditer(line_lyric)
            line_out=''
            for char in char_list:
                char,char_start=char.groups()
                line_out+=f'[{format_time(int(char_start))}]{char}'
            line_out+=f'[{format_time(int(line_start)+int(line_dur))}]'
            lrc_out+=f'{line_out}\n'            

            line_out=line_ch_res.group(3)
            line_out=repl_re.sub('',line_out)
            lrc_out+=f'[{format_time(int(line_start)+int(line_dur)-20)}]{line_out}\n'

        lrc_output('mix',line_ign,lrc_out,'mix')
        return 0

def format_time(ts):
    # # 时间戳，三位小数兼容性不足，换用两位小数
    # return f'{ts//60000:02d}:{(ts//1000)%60:02d}.{ts%1000:03d}'
    # 时间戳小数部分，从向下取整变为四舍五入
    ts=round(ts/10)*10            
    return f'{ts//60000:02}:{(ts//1000)%60:02}.{ts%1000//10:02}'

def lrc_output(language_type,line_ign,lrc_out,lrc_type):
    dic = {'orig':'og','roma':'rm','ts':'ch','mix':'og&ch'}
    f=open(f'{lrc_path}/{title}-{dic[language_type]}-{lrc_type}-ignr.txt', mode='w', encoding='utf-8')
    f.write(line_ign)
    f.close()

    f=open(f'{lrc_path}/{title}-{dic[language_type]}-{lrc_type}.lrc', mode='w', encoding='utf-8')
    f.write(lrc_out)
    f.close()    

def main():
    global title
    title=input('(Input nothing to exit...)\n@ Title: ')
    if title=='':
        return 1
    artist=input('(Fill or leave a blank...)\n@ Artist: ')
    print('@ Searching...')
    songlist=list(query_lyric(title,artist))
    for ind,song in enumerate(songlist):
        print('#%d: (%s) %s / %s / %s'%(ind,song['songid'],song['name'],song['singer'],song['album']))
    cid=input('(Input nothing to cancel...)\n@ Select: #')
    if cid=='':
        print('* No selection, next song waiting...')
        return 0
    songid=songlist[int(cid)]['songid']
    # print('Song ID = %s'%songid)
    print('@ Downloading...')

    # 加入unix时间戳防止输出被重复覆盖
    unix_time = str(int(time.time()))
    list_path=root_path+f'/lyric/{title}-{artist}'
    global lrc_path
    lrc_path = list_path+f'/{cid}-{unix_time}'
    os.makedirs(lrc_path,exist_ok=True)

    f=open(list_path+f'/{title}-{artist}-idlist.txt', mode='w', encoding='utf-8')
    song_list=''
    for ind,song in enumerate(songlist):
        song_list += '#%d: (%s) %s / %s / %s\n'%(ind,song['songid'],song['name'],song['singer'],song['album'])
    f.write(song_list)
    f.close()

    res=fetch_lyric_by_id(songid,['orig','roma','ts'])
    # # output original decode text
    # # warning: will overwrite
    # for typ,data in res.items():
    #     f=open(root_path+f'/lyric/{typ}_decode.lrc', mode='w', encoding='utf-8')
    #     f.write(data)
    #     f.close()

    if down_lyric_mix(res) == 1:
        print('! Failed, next song waiting... !')
        return 0
    down_lyric_line(res)
    down_lyric_char(res)
    print('@ Complete, next song waiting...')
    return 0

if __name__=='__main__':
    # quit when main() return 1
    while not main():
        pass
