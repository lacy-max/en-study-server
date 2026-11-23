# -*- coding: utf-8 -*-
"""交叉页段落校验（第一人称叙述体）。

规则与 content_check.py 一致：句子里的词只能来自
  1) 前序单元已学词（含全部 L0）
  2) 本单元任意词
  3) 语法骨架词 FUNCTION
  4) 人名称谓 NAMES
  5) 固定礼貌语块
另外检查：句长 ≤7、每段 3–5 句、每段至少 2 个本课词、中文齐全。

用法: python3 tools/passage_check.py
"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from content_check import FUNCTION, NAMES, PHRASES, _lemmas, tokens  # noqa: E402
from l1_passages import PASSAGES  # noqa: E402

MAX_WORDS = 7
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "chapters.json")


def main():
    units = json.load(open(DATA, encoding="utf-8"))
    taught = set()
    problems = []
    warns = []
    covered = {}
    for u in units:
        level = str(u.get("level") or "L0").upper()
        words = [str(w.get("en", "")).strip().lower() for w in u.get("words", [])]
        if level == "L0":
            taught |= set(words)
            continue
        unit_words = set(words)
        allowed = FUNCTION | NAMES | taught | unit_words

        passages = PASSAGES.get(u["id"])
        if not passages:
            problems.append("[%s] 缺段落（应 3 段）" % u["id"])
            taught |= unit_words
            continue
        if len(passages) != 3:
            problems.append("[%s] 段落数 %d，应为 3" % (u["id"], len(passages)))

        hit = set()
        for pi, p in enumerate(passages, 1):
            lines = p.get("lines", [])
            tag = "[%s] 段%d %s" % (u["id"], pi, p.get("title"))
            if not (3 <= len(lines) <= 5):
                problems.append("%s: %d 句，应为 3–5 句" % (tag, len(lines)))
            local = set()
            for en, cn in lines:
                toks = tokens(en)
                punct = re.split(r"[^A-Za-z']+", en.strip(" .!?"))
                if len(toks) > MAX_WORDS:
                    problems.append("%s: 句长 %d 词 > %d · %s" % (tag, len(toks), MAX_WORDS, en))
                if not cn.strip():
                    problems.append("%s: 缺中文 · %s" % (tag, en))
                if not toks:
                    continue
                core = " ".join(t for t in toks if t not in NAMES)
                if core in PHRASES:
                    continue
                for t in toks:
                    if t.endswith("'s"):
                        t = t[:-2]
                    if t in allowed:
                        continue
                    if any(l in allowed for l in _lemmas(t)):
                        continue
                    problems.append("%s: 超纲词 '%s' · %s" % (tag, t, en))
                for t in toks:
                    base = t[:-2] if t.endswith("'s") else t
                    if base in unit_words or any(l in unit_words for l in _lemmas(base)):
                        local.add(base if base in unit_words else next(l for l in _lemmas(base) if l in unit_words))
            hit |= local
            covered.setdefault(u["id"], []).append((pi, len(local), sorted(local)))
            if len(local) < 2:
                problems.append("%s: 本课词只有 %d 个（%s）" % (tag, len(local), ", ".join(sorted(local)) or "无"))
            elif len(local) > 4:
                warns.append("%s: 本课词 %d 个（%s）" % (tag, len(local), ", ".join(sorted(local))))
        miss = sorted(unit_words - hit)
        if miss:
            warns.append("[%s] 段落未涉及的本课词 %d 个: %s" % (u["id"], len(miss), ", ".join(miss)))
        taught |= unit_words

    print("单元 %d · 段落 %d · 句 %d" % (
        len(PASSAGES), sum(len(v) for v in PASSAGES.values()),
        sum(len(p["lines"]) for v in PASSAGES.values() for p in v)))
    if warns:
        print("\n--- 提示 %d 条 ---" % len(warns))
        for w in warns[:40]:
            print("  ", w)
    if problems:
        print("\n!!! 问题 %d 条 !!!" % len(problems))
        for p in problems[:80]:
            print("  ", p)
        sys.exit(1)
    print("\n✔ 0 个问题")


if __name__ == "__main__":
    main()
