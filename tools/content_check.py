# -*- coding: utf-8 -*-
"""题库内容校验（逐词递进版）
规则：一个词的例句，只能用
  1) 前序单元已学过的词
  2) 本单元中排在它前面的词
  3) 语法骨架词（冠词/系动词/代词/介词/连词/助动词）
  4) 人名与家庭称谓
  5) 固定礼貌语块（整块输入，如 Good morning / No, thanks）
用法: python3 tools/content_check.py [data/chapters.json]
"""
import json, re, sys

FUNCTION = set("""a an the is am are be i you we he she it my your his her our
this that these those in on at to of and or not can do does let us what how very so here there
me my mine him them have has with for
""".split())

NAMES = set("""tom lily sam amy bob ben lucy mimi mum dad""".split())

# 固定语块（allow 跨序使用，视为一次整体输入）
PHRASES = set("""yes please|no thanks|ok thanks|good morning|good night|thank you|good thanks
""".replace('\n', '').split('|'))

MAX_WORDS = {'L0': 5, 'L1': 6, 'L2': 8, 'L3': 10, 'L4': 12, 'L5': 15, 'L6': 18}

def tokens(text):
    return [t for t in re.split(r"[^A-Za-z']+", text.lower()) if t]

IRREGULAR = {'teeth': 'tooth', 'feet': 'foot', 'men': 'man', 'women': 'woman', 'children': 'child'}

def _lemmas(t):
    out = []
    if t in IRREGULAR:
        out.append(IRREGULAR[t])
    if t.endswith('ies'):
        out.append(t[:-3] + 'y')
    if t.endswith('es'):
        out.append(t[:-2])
    if t.endswith('s'):
        out.append(t[:-1])
    return out or [t]

def check(path):
    units = json.load(open(path, encoding='utf-8'))
    taught = set()
    problems = []
    stats = {'units': len(units), 'words': 0, 'sentences': 0}
    for u in units:
        level = str(u.get('level') or 'L0').upper()
        words = u.get('words', [])
        stats['words'] += len(words)
        seen_in_unit = set()
        for w in words:
            en = str(w.get('en', '')).strip()
            key = en.lower()
            sent = str(w.get('sentence') or '').strip()
            sent_cn = str(w.get('sentenceCn') or '').strip()
            if not sent:
                problems.append(f"[{u['id']}] {en}: 缺例句")
                seen_in_unit.add(key)
                continue
            stats['sentences'] += 1
            toks = tokens(sent)
            maxw = MAX_WORDS.get(level, 6)
            if len(toks) > maxw:
                problems.append(f"[{u['id']}] {en}: 例句过长 {len(toks)} 词 > {maxw} · {sent}")
            if not sent_cn:
                problems.append(f"[{u['id']}] {en}: 缺中文句意")
            if key not in toks and not any(key in _lemmas(t) for t in toks):
                problems.append(f"[{u['id']}] {en}: 例句里没有目标词 · {sent}")
            core = ' '.join(t for t in toks if t not in NAMES)
            if core not in PHRASES:
                allowed = FUNCTION | NAMES | taught | seen_in_unit | {key}
                for t in toks:
                    if t not in allowed and not any(l in allowed for l in _lemmas(t)):
                        problems.append(f"[{u['id']}] {en}: 超纲词 '{t}' · {sent}")
            seen_in_unit.add(key)
        taught |= set(str(w.get('en', '')).strip().lower() for w in words)
    return stats, problems

if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'data/chapters.json'
    stats, problems = check(path)
    print(f"单元 {stats['units']} · 单词 {stats['words']} · 例句 {stats['sentences']} · 问题 {len(problems)}")
    for p in problems:
        print('  ' + p)
