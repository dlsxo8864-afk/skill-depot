"""Build sentence beats and readable caption groups from measured alignment."""
from pathlib import Path
import json, math, subprocess
ROOT=Path(__file__).resolve().parents[1]
episodes=json.loads((ROOT/'episodes.json').read_text(encoding='utf-8'))['episodes']
def stamp(t):
    ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
for e in episodes:
    out=ROOT/'episodes'/f"ep{e['ep']}"
    result=json.loads((out/'alignment-original.json').read_text(encoding='utf-8'))
    chars=result['characters'];transcript=''.join(c['text'] for c in chars)
    expected=' '.join(e['lines']);assert transcript==expected,(e['ep'],transcript,expected)
    speed=1.18 if e['ep']==5 else 1
    duration=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(out/'narration.wav')]))
    frames=math.ceil((duration+.45)*24)
    assert frames<=720, 'Voice needs editorial adjustment before animation'
    captions=[];scenes=[];offset=0
    for i,(line,beat) in enumerate(zip(e['lines'],e['beats'])):
        part=chars[offset:offset+len(line)]
        start=part[0]['start']/speed
        scenes.append({'id':beat,'line':line,'startFrame':0 if i==0 else round(start*24),'startSec':0 if i==0 else round(start*24)/24})
        cursor=0
        while cursor<len(line):
            end=min(len(line),cursor+14)
            if end<len(line):
                boundary=line.rfind(' ',cursor+6,end+1)
                if boundary>cursor:end=boundary
            phrase=line[cursor:end].strip()
            if phrase:
                start_ms=round(part[cursor]['start']/speed*1000)
                end_ms=round(max(part[end-1]['end']/speed,part[cursor]['start']/speed+.12)*1000)
                captions.append({'text':phrase,'startMs':start_ms,'endMs':end_ms,'timestampMs':None,'confidence':None,'pageBreakAfter':True})
            cursor=end
            while cursor<len(line) and line[cursor]==' ':cursor+=1
        offset+=len(line)+1
    for i,s in enumerate(scenes):
        s['endFrame']=scenes[i+1]['startFrame'] if i+1<len(scenes) else frames
        s['endSec']=s['endFrame']/24
    for i,c in enumerate(captions):
        nxt=captions[i+1]['startMs'] if i+1<len(captions) else round(duration*1000)
        c['endMs']=min(nxt,c['endMs']+120)
        assert c['startMs']<c['endMs'] and c['endMs']<=frames/24*1000
    (out/'captions.json').write_text(json.dumps(captions,ensure_ascii=False,indent=2),encoding='utf-8')
    timeline={'version':2,'ep':e['ep'],'title':e['title'],'fps':24,'width':1080,'height':1920,'frames':frames,'durationSeconds':frames/24,'voiceDurationSeconds':duration,'voiceSpeed':speed,'alignmentMethod':'ElevenLabs forced alignment of full supplied transcript; speed correction applied','cast':e['cast'],'scenes':scenes}
    (out/'timeline.json').write_text(json.dumps(timeline,ensure_ascii=False,indent=2),encoding='utf-8')
    (out/f"EP{e['ep']}-자막.srt").write_text('\n\n'.join(f"{i+1}\n{stamp(c['startMs']/1000)} --> {stamp(c['endMs']/1000)}\n{c['text']}" for i,c in enumerate(captions))+'\n',encoding='utf-8-sig')
    print(e['ep'],frames,len(captions),[(s['id'],s['startFrame'],s['endFrame']) for s in scenes])

