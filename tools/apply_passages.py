# -*- coding: utf-8 -*-
"""把 tools/l1_passages.py 的段落写进 data/chapters.json（L1 各课的 passages 字段）。

用法:
    python3 tools/apply_passages.py            # 写入 + 自动备份
    python3 tools/apply_passages.py --dry      # 只统计不写

写入结构（每课 3 段）：
    "passages": [
      {"title": "我是新来的", "scene": "...",
       "lines": [{"en": "...", "cn": "..."}, ...]},
    ]
入库后务必再跑：python3 tools/passage_check.py && python3 tools/content_check.py
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1_passages import PASSAGES  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "chapters.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    units = json.load(io.open(DATA, encoding="utf-8"))
    written = 0
    for u in units:
        if str(u.get("level", "")).upper() != "L1":
            continue
        ps = PASSAGES.get(u["id"])
        if not ps:
            print("跳过（无段落）：", u["id"])
            continue
        u["passages"] = [
            {"title": p["title"], "scene": p["scene"],
             "lines": [{"en": en, "cn": cn} for en, cn in p["lines"]]}
            for p in ps
        ]
        written += 1

    total_p = sum(len(u.get("passages") or []) for u in units)
    total_l = sum(len(p["lines"]) for u in units for p in (u.get("passages") or []))
    print("写入 %d 课 · 段落 %d · 句 %d" % (written, total_p, total_l))
    if args.dry:
        print("--dry，未落盘")
        return
    bak = DATA.replace(".json", ".backup-段落入库前.json")
    if not os.path.exists(bak):
        io.open(bak, "w", encoding="utf-8").write(io.open(DATA, encoding="utf-8").read())
        print("备份：", os.path.basename(bak))
    with io.open(DATA, "w", encoding="utf-8") as f:
        json.dump(units, f, ensure_ascii=False, indent=1)
    print("写入完成：", DATA, datetime.now().strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
