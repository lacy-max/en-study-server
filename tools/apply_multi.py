# -*- coding: utf-8 -*-
"""把 tools/l1_multi.py 的三句写进 data/chapters.json（每个词条加 sentences）。

用法:
    python3 tools/apply_multi.py          # 写入 + 备份
    python3 tools/apply_multi.py --dry

写入结构：
    "sentences": [{"en": "...", "cn": "..."}, {"en": "..."}, {"en": "..."}]
同时把 sentence / sentenceCn 设为第 1 句，保持旧字段兼容（列表、搜索、朗读都用它）。
入库后：python3 tools/multi_check.py && python3 tools/content_check.py
"""
import argparse
import io
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from l1_multi import MULTI  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "chapters.json")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry", action="store_true")
    args = ap.parse_args()

    units = json.load(io.open(DATA, encoding="utf-8"))
    words_written = 0
    for u in units:
        if str(u.get("level", "")).upper() != "L1":
            continue
        data = {k.lower(): v for k, v in (MULTI.get(u["id"]) or {}).items()}
        if not data:
            continue
        for w in u.get("words", []):
            ss = data.get(str(w.get("en", "")).strip().lower())
            if not ss:
                continue
            w["sentences"] = [{"en": en, "cn": cn} for en, cn in ss]
            w["sentence"] = ss[0][0]
            w["sentenceCn"] = ss[0][1]
            words_written += 1

    total = sum(len(w.get("sentences") or []) for u in units for w in u.get("words", []))
    print("写入 %d 词 · %d 句" % (words_written, total))
    if args.dry:
        print("--dry，未落盘")
        return
    bak = DATA.replace(".json", ".backup-三句入库前.json")
    if not os.path.exists(bak):
        io.open(bak, "w", encoding="utf-8").write(io.open(DATA, encoding="utf-8").read())
        print("备份：", os.path.basename(bak))
    with io.open(DATA, "w", encoding="utf-8") as f:
        json.dump(units, f, ensure_ascii=False, indent=1)
    print("写入完成：", DATA, datetime.now().strftime("%H:%M:%S"))


if __name__ == "__main__":
    main()
