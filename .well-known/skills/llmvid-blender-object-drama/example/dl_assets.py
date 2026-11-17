"""Poly Haven CC0 소재 내려받기. 인자: 저장 폴더

사용: python dl_assets.py <소재 폴더>
- api.polyhaven.com 에서 아래 MODELS(gltf)·나무/벽 텍스처(2k jpg)·HDRI(2k)를 받는다. 약 31MB.
- 인터넷에서 파일을 내려받는 일이므로 사용자 허가를 받은 뒤에만 돌린다.
- 이미 있는 파일은 건너뛴다(끊겨도 다시 돌리면 이어서 받는다).
- 결과 폴더(models/, tex/, hdri/)를 build 스크립트의 --assets 로 넘긴다.
"""
import json
import os
import sys
import urllib.request

if len(sys.argv) < 2:
    raise SystemExit("사용: python dl_assets.py <소재 폴더>")
root = sys.argv[1]
UA = {"User-Agent": "blender-skill-test/1.0"}


def api(path):
    return json.load(urllib.request.urlopen(urllib.request.Request("https://api.polyhaven.com/" + path, headers=UA), timeout=60))


def get(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=180) as r, open(dest + ".part", "wb") as f:
        while True:
            b = r.read(1 << 20)
            if not b:
                break
            f.write(b)
    os.replace(dest + ".part", dest)


# 이 장면(build_ssul.py)이 쓰는 소품만 받는다. (이름, 해상도)
MODELS = [("desk_lamp_arm_01", "1k"), ("classic_laptop", "1k"), ("office_notepads", "1k"), ("alarm_clock_01", "1k")]
for name, res in MODELS:
    files = api(f"files/{name}")
    if "gltf" not in files:
        print("SKIP no gltf", name, list(files.keys()), flush=True)
        continue
    g = files["gltf"][res]["gltf"]
    d = os.path.join(root, "models", name)
    get(g["url"], os.path.join(d, os.path.basename(g["url"])))
    for rel, f in g["include"].items():
        get(f["url"], os.path.join(d, rel))
    print("model", name, flush=True)

for name, maps in [("wood_table_worn", ("Diffuse", "nor_gl", "Rough")), ("painted_plaster_wall", ("Diffuse", "nor_gl", "Rough"))]:
    f = api(f"files/{name}")
    for k in maps:
        u = f[k]["2k"]["jpg"]["url"]
        get(u, os.path.join(root, "tex", name, os.path.basename(u)))
    print("tex", name, [k for k in f.keys()][:8], flush=True)

u = api("files/studio_small_09")["hdri"]["2k"]["hdr"]["url"]
get(u, os.path.join(root, "hdri", os.path.basename(u)))
print("hdri ok", flush=True)
