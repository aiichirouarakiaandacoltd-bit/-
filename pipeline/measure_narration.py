"""台本係の道具: scenes.json のナレーションを VOICEVOX(青山龍星0.90)で合成し、場面ごとと合計の秒数を出す。python pipeline/measure_narration.py <制作番号>"""
import json,sys
sys.path.insert(0,'.')
from pipeline.rules_render import tts, speaker_id
from pipeline.common import load_json
P='projects/'+sys.argv[1]
r={k:v for k,v in load_json('config/reading_dict.json').items() if not k.startswith('_')}; r.update(load_json(P+'/readings.json',{}))
sid=speaker_id(); tot=0.25+0.6
for s in json.load(open(P+'/scenes.json',encoding='utf-8')):
    d=len(tts(s['narration'],sid,r))/48000; tot+=d+0.12; print(s['scene'],round(d,2),s['narration'])
print('合計',round(tot,2))
