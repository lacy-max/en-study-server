# -*- coding: utf-8 -*-
"""每词 3 句校验（人工撰写版）。

规则与 content_check.py 完全一致：前序单元已学词 + 本课词 + 骨架词 + 人名。
另外检查：单句 ≤7 词、每句含目标词、中文齐全、每词 3 句、单课开头重复 ≤3。

用法: python3 tools/multi_check.py
"""
import json
import os
import re
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content_check import FUNCTION, NAMES, PHRASES, _lemmas, tokens  # noqa: E402
from l1_multi import MULTI  # noqa: E402

MAX_WORDS = 7
NEED = 3
OPENER_MAX = 3
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "chapters.json")


def main():
    units = json.load(open(DATA, encoding="utf-8"))
    taught = set()
    problems, warns = [], []
    done_units, done_words = 0, 0
    for u in units:
        level = str(u.get("level") or "L0").upper()
        words = [str(w.get("en", "")).strip().lower() for w in u.get("words", [])]
        if level == "L0":
            taught |= set(words)
            continue
        data = {k.lower(): v for k, v in (MULTI.get(u["id"]) or {}).items()} or None
        if data:
            done_units += 1
            allowed = FUNCTION | NAMES | taught | set(words)
            if set(data) != set(words):
                miss = sorted(set(words) - set(data))
                extra = sorted(set(data) - set(words))
                if miss:
                    problems.append("[%s] 缺词: %s" % (u["id"], ", ".join(miss)))
                if extra:
                    problems.append("[%s] 多出词: %s" % (u["id"], ", ".join(extra)))
            openers = Counter()
            for w in u["words"]:
                en = str(w.get("en", "")).strip()
                key = en.lower()
                ss = data.get(key)
                if not ss:
                    continue
                done_words += 1
                if len(ss) != NEED:
                    problems.append("[%s] %s: %d 句，应为 %d" % (u["id"], en, len(ss), NEED))
                for i, (sent, cn) in enumerate(ss, 1):
                    toks = tokens(sent)
                    tag = "[%s] %s 句%d" % (u["id"], en, i)
                    if len(toks) > MAX_WORDS:
                        problems.append("%s: 句长 %d > %d · %s" % (tag, len(toks), MAX_WORDS, sent))
                    if not cn.strip():
                        problems.append("%s: 缺中文 · %s" % (tag, sent))
                    if not toks:
                        continue
                    data_core = " ".join(t for t in toks if t not in NAMES)
                    if data_core in PHRASES:
                        continue
                    hit = key in toks or any(key in _lemmas(t) for t in toks)
                    if not hit:
                        problems.append("%s: 缺目标词 · %s" % (tag, sent))
                    for t in toks:
                        t2 = t[:-2] if t.endswith("'s") else t
                        if t2 in allowed:
                            continue
                        if any(l in allowed for l in _lemmas(t2)):
                            continue
                        problems.append("%s: 超纲词 '%s' · %s" % (tag, t2, sent))
                    if i == 1:
                        openers[toks[0]] += 1
            for op, n in openers.items():
                if n > OPENER_MAX:
                    warns.append("[%s] 开头 '%s' 用了 %d 次" % (u["id"], op, n))
        taught |= set(words)

    covered = sum(len(v) for v in MULTI.values())
    print("已写 %d 课 / %d 词 / %d 句（覆盖率 %d/%d 课）" % (
        done_units, covered, done_words, done_units, len(MULTI)))
    if warns:
        print("\n--- 提示 %d 条 ---" % len(warns))
        for w in warns[:30]:
            print("  ", w)
    if problems:
        print("\n!!! 问题 %d 条 !!!" % len(problems))
        for p in problems[:80]:
            print("  ", p)
        sys.exit(1)
    print("\n✔ 0 个问题")


if __name__ == "__main__":
    main()
