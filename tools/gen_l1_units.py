# -*- coding: utf-8 -*-
"""把 l1_sentences.py 的例句贴回 L1 词表，生成 l1_units.py。改句子只改 l1_sentences.py。"""
import io, json, sys
sys.path.insert(0, 'tools')
from l1_sentences import SENT

data = json.load(open('data/chapters.json', encoding='utf-8'))
l1 = [u for u in data if u['level'] == 'L1']
out = ['# -*- coding: utf-8 -*-',
       '"""L1 小学低段 24 单元 × 15 词 = 360 词（例句见 l1_sentences.py）。"""',
       '', 'UNITS_L1 = [']
for i, u in enumerate(l1, 1):
    out.append("  ('%s', 'L1', '%s', 'L1 小学低段 · 15 个词 · 第 %d 课', [" % (u['id'], u['title'], i))
    for w in u['words']:
        s, sc = SENT[w['en']]
        out.append("    ('%s', '%s', '%s', '%s', '%s')," % (w['en'], w['cn'], s, sc, w['emoji']))
    out.append("  ]),")
    out.append("")
out.append(']')
io.open('tools/l1_units.py', 'w', encoding='utf-8').write("\n".join(out) + "\n")
print('l1_units.py 已更新')
