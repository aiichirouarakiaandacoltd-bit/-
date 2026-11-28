import sys, json; sys.path.insert(0, "/home/user/-/research/LONG-20261124/deep/scripts")
import yt
SHORTS_TAB = "EgZzaG9ydHPyBgUKA5oBAA%3D%3D"
d = yt.api("browse", {"browseId": "UCXbDey6pEEbrXl4RQ32CcDw", "params": "EgZzaG9ydHPyBgUKA5oBAA=="})
keys = set()
def scan(o):
    if isinstance(o, dict):
        for k, v in o.items():
            if k.endswith("ViewModel") or k.endswith("Renderer"): keys.add(k)
            scan(v)
    elif isinstance(o, list):
        for v in o: scan(v)
scan(d); print(sorted(k for k in keys if "hort" in k or "eel" in k or "ockup" in k or "chip" in k.lower()))
s = next(yt.walk(d, "shortsLockupViewModel"), None); print(json.dumps(s, ensure_ascii=False)[:1500])
