# -*- coding: utf-8 -*-
"""批量生成 L1 交叉页段落音频（按说话人分配音色）。

用法（需要 edge-tts：pip install edge-tts）：
    python3 tools/gen_audio.py                      # 生成全部课
    python3 tools/gen_audio.py --units unit31,unit32
    python3 tools/gen_audio.py --units unit31 --force   # 覆盖已存在

产物：
    static/audio/l1/unit31/p1/l01.mp3   单句（点角色头像可单听）
    static/audio/l1/unit31/p1.mp3       整段拼接（顺序自动播放）
    static/audio/l1/index.json          前端索引（含说话人、中英文）

音色零成本（Edge 朗读服务），一次性生成即可，之后不再调用。
"""
import argparse
import asyncio
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1_passages import PASSAGES, ROLE_CN  # noqa: E402

try:
    import edge_tts
except ImportError:
    sys.exit("缺少 edge-tts，先执行：python3 -m pip install edge-tts")

# 说话人 → 音色（已试听确认：Tom 用 GuyNeural 提音调更像男孩）
VOICE = {
    "lily":    dict(voice="en-US-AnaNeural",       rate="+0%",  pitch="+0Hz"),
    "tom":     dict(voice="en-US-GuyNeural",       rate="+0%",  pitch="+30Hz"),
    "mum":     dict(voice="en-US-AriaNeural",      rate="+0%",  pitch="+0Hz"),
    "dad":     dict(voice="en-US-ChristopherNeural", rate="+0%", pitch="+0Hz"),
    "teacher": dict(voice="en-US-JennyNeural",     rate="+0%",  pitch="+0Hz"),
    "grandma": dict(voice="en-US-JennyNeural",     rate="-10%", pitch="-8Hz"),
    "grandpa": dict(voice="en-US-ChristopherNeural", rate="-12%", pitch="-10Hz"),
}

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DEFAULT = os.path.join(ROOT, "static", "audio", "l1")


async def _tts(text, spk, path):
    cfg = VOICE[spk]
    await edge_tts.Communicate(text, cfg["voice"],
                               rate=cfg["rate"], pitch=cfg["pitch"]).save(path)


async def build_unit(unit, passages, out_root, force=False):
    index = []
    for pi, p in enumerate(passages, 1):
        pdir = os.path.join(out_root, unit, "p%d" % pi)
        os.makedirs(pdir, exist_ok=True)
        parts = []
        lines = []
        for li, ln in enumerate(p["lines"], 1):
            rel = "p%d/l%02d.mp3" % (pi, li)
            path = os.path.join(out_root, unit, rel)
            if force or not os.path.exists(path):
                await _tts(ln["en"], ln["spk"], path)
            parts.append(path)
            lines.append(dict(spk=ln["spk"], role=ROLE_CN.get(ln["spk"], ln["spk"]),
                              en=ln["en"], cn=ln["cn"], file=rel))
        merged_rel = "p%d.mp3" % pi
        merged = os.path.join(out_root, unit, merged_rel)
        if force or not os.path.exists(merged):
            with open(merged, "wb") as f:
                for pt in parts:
                    with open(pt, "rb") as g:
                        f.write(g.read())
        index.append(dict(title=p["title"], scene=p["scene"],
                          audio=merged_rel, lines=lines))
    return index


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--units", default="", help="逗号分隔，如 unit31,unit32")
    ap.add_argument("--out", default=OUT_DEFAULT)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    units = [u.strip() for u in args.units.split(",") if u.strip()] or list(PASSAGES)
    os.makedirs(args.out, exist_ok=True)
    index_path = os.path.join(args.out, "index.json")
    idx = {}
    if os.path.exists(index_path):
        with io.open(index_path, encoding="utf-8") as f:
            idx = json.load(f)

    for u in units:
        if u not in PASSAGES:
            print("跳过（无段落数据）：%s" % u)
            continue
        idx[u] = asyncio.run(build_unit(u, PASSAGES[u], args.out, args.force))
        n = sum(len(p["lines"]) for p in idx[u])
        print("%s  %d 段 / %d 句  完成" % (u, len(idx[u]), n))

    with io.open(index_path, "w", encoding="utf-8") as f:
        json.dump(idx, f, ensure_ascii=False, indent=1)
    print("索引写入 %s（%d 课）" % (index_path, len(idx)))


if __name__ == "__main__":
    main()
