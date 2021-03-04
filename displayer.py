import qrcd
import re
from flask import *
from flask_socketio import SocketIO, emit

app=Flask(__name__)
app.debug=True

sio=SocketIO(app)

qrc_line_re=re.compile(r'^\[(\d+),(\d+)\](.*)$')
qrc_chunk_re=re.compile(r'^(.*)\((\d+),(\d+)$')

@app.route('/')
def search():
    return render_template('search.html')
    
@app.route('/api/search',methods=['POST'])
def api_search():
    json=request.json
    try:
        res=list(qrcd.query_lyric(json['name'],json['singer']))
    except Exception as e:
        return f'{type(e)} {e}'
    else:
        return render_template('result_widget.html',
            result=res,
        )

@app.route('/player')
def player():
    return render_template('player.html')

@app.route('/api/get_lyric/<int:songid>')
def api_get_lyric(songid):
    lrc=qrcd.fetch_lyric_by_id(songid,['orig','roma','ts'])

    def parse_qrc(data):
        INF=2147483647

        line_src=[]
        chunk_src=[]
        line_action=[]
        chunk_action=[]
        chunk_time=[]
        line_time=[]

        def apply_chunk(data,time_s,dt):
            if data=='//':
                return
            chunkid=len(chunk_src)
            line_src[-1].append(chunkid)
            chunk_src.append(data)
            chunk_time.append(time_s/1000 if time_s is not None else None)
            if time_s is not None:
                chunk_action.append([time_s,True,chunkid])
                chunk_action.append([time_s+dt,False,chunkid])

        line_src.append([])
        line_action.append([-INF,False,0])
        line_action.append([INF,True,0])
        chunk_action.append([-INF,False,0])
        chunk_action.append([INF,True,0])
        chunk_src.append(None)
        chunk_time.append(0)
        line_time.append(0)

        for line_s in data.split('\n'):
            line=qrc_line_re.match(line_s)
            if not line:
                print('ignored LINE:',line_s)
                continue

            time_s,dt,content=line.groups()
            time_s=int(time_s)
            dt=int(dt)
            lineid=len(line_src)
            line_src.append([])
            line_time.append(time_s/1000)

            line_action.append([time_s,True,lineid])
            line_action.append([time_s+dt,False,lineid])

            splited_content=content.split(')')
            for ind,chunk_s in enumerate(splited_content):
                chunk=qrc_chunk_re.match(chunk_s)
                if not chunk:
                    if len(splited_content)==ind+1: # last chunk without timestamp
                        if chunk_s:
                            apply_chunk(chunk_s,None,None)
                    else: # notmal ')'
                        splited_content[ind+1]=chunk_s+')'+splited_content[ind+1]
                    continue

                content,time_s,dt=chunk.groups()
                time_s=int(time_s)
                dt=int(dt)
                apply_chunk(content,time_s,dt)

        line_action.sort(key=lambda x:x[0])
        chunk_action.sort(key=lambda x:x[0])

        return {
            'line_src': line_src,
            'chunk_src': chunk_src,
            'line_action': line_action,
            'chunk_action': chunk_action,
            'chunk_time': chunk_time,
            'line_time': line_time,
        }

    return jsonify(
        orig=parse_qrc(lrc['orig']),
        roma=parse_qrc(lrc['roma']),
        ts=parse_qrc(lrc['ts']),
    )

@app.route('/down_lyric/orig/<int:songid>')
def down_lyric_orig(songid):
    lrc=qrcd.fetch_lyric_by_id(songid,['orig'])['orig']
    
    line_re=re.compile(r'^\[(\d+),\d+\](.*)$')
    repl_re=re.compile(r'\(\d+,\d+\)')
    
    out=''
    
    def format_time(ts):
        return f'{ts//60000}:{(ts//1000)%60:02d}.{ts%1000:03d}'
    
    for line in lrc.splitlines():
        line_res=line_re.match(line)
        if not line_res:
            print('ignoring line',line)
            continue
        start_ts,content=line_res.groups()
        content=repl_re.sub('',content)
        out+=f'[{format_time(int(start_ts))}]{content}\n'

    return Response(
        out,
        mimetype='text/plain',
    )

@sio.on('master_update')
def sio_master_update(msg):
    emit('master_update',msg,broadcast=True,include_self=False)
    
@sio.on('slave_update')
def sio_slave_update(msg):
    emit('slave_update',msg,broadcast=True,include_self=False)

sio.run(app,'0.0.0.0',80)