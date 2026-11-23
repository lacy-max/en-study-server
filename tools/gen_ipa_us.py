# -*- coding: utf-8 -*-
"""生成美式音标（Cambridge 美式口径）写回 chapters.json 的 ipaUs 字段。
英式音标沿用已有 ipa 字段。
用法: python3 tools/gen_ipa_us.py
"""
import json, io, re, cmudict

P = 'data/chapters.json'
D = cmudict.dict()

CONS = {'B': 'b', 'CH': 'tʃ', 'D': 'd', 'DH': 'ð', 'F': 'f', 'G': 'g', 'H': 'h', 'HH': 'h',
        'JH': 'dʒ', 'K': 'k', 'L': 'l', 'M': 'm', 'N': 'n', 'NG': 'ŋ', 'P': 'p', 'S': 's',
        'SH': 'ʃ', 'T': 't', 'TH': 'θ', 'V': 'v', 'W': 'w', 'X': 'ks', 'Y': 'j', 'Z': 'z',
        'ZH': 'ʒ', 'Q': 'k'}
VOW = {'AA', 'AE', 'AH', 'AO', 'AW', 'AY', 'EH', 'ER', 'EY', 'IH', 'IY', 'OW', 'OY', 'UH', 'UW'}

LEGAL3 = {'str', 'spr', 'skr', 'spl', 'shr', 'thr', 'squ'}
LEGAL2 = {'st', 'sp', 'sk', 'sl', 'sm', 'sn', 'sw', 'bl', 'br', 'cl', 'cr', 'dr', 'fl', 'fr',
          'gl', 'gr', 'pl', 'pr', 'tr', 'tw', 'th', 'ch', 'sh', 'wh', 'wr', 'kn', 'gn', 'ph', 'qu'}

# 人工校正（Cambridge 美式）
OVERRIDE = {
    'tomato': 'təˈmeɪtoʊ', 'water': 'ˈwɑːtɚ', 'class': 'klæs', 'glasses': 'ˈglæsɪz',
    'classmate': 'ˈklæsmeɪt', 'classroom': 'ˈklæsruːm', 'answer': 'ˈænsɚ',
    'after': 'ˈæftɚ', 'afternoon': 'ˌæftɚˈnuːn', 'aunt': 'ɔːnt', 'laugh': 'lɔːf',
    'new': 'nuː', 'student': 'ˈstuːdənt', 'Tuesday': 'ˈtuːzdeɪ', 'duty': 'ˈduːti',
    'library': 'ˈlaɪbreri', 'February': 'ˈfebrueri', 'Wednesday': 'ˈwednzdeɪ',
    'orange': 'ˈɔːrɪndʒ', 'sorry': 'ˈsɔːri', 'borrow': 'ˈbɔːroʊ', 'tomorrow': 'təˈmɔːroʊ',
    'giraffe': 'dʒəˈræf', 'zebra': 'ˈziːbrə', 'penguin': 'ˈpeŋgwɪn', 'kangaroo': 'ˌkæŋgəˈruː',
    'koala': 'koʊˈɑːlə', 'elephant': 'ˈeləfənt', 'apartment': 'əˈpɑːrtmənt',
    'parents': 'ˈperənts', 'daughter': 'ˈdɔːtɚ', 'watermelon': 'ˈwɔːtɚmelən',
    'avocado': 'ˌɑːvəˈkɑːdoʊ', 'yogurt': 'ˈjoʊgɚt', 'humid': 'ˈhjuːmɪd', 'minute': 'ˈmɪnɪt',
    'second': 'ˈsekənd', 'forest': 'ˈfɔːrɪst', 'island': 'ˈaɪlənd', 'autumn': 'ˈɔːtəm',
    'daughter-in-law': 'ˈdɔːtɚ ɪn lɔː', 'pajamas': 'pəˈdʒɑːməz', 'pyjamas': 'pəˈdʒɑːməz',
    'maths': 'mæθs', 'mooncake': 'ˈmuːnkeɪk', 'schoolbag': 'ˈskuːlbæg',
    'everyone': 'ˈevriwʌn', 'everybody': 'ˈevribɑːdi', 'grandma': 'ˈgrænmɑː',
    'grandpa': 'ˈgrænpɑː', 'grandmother': 'ˈgrænmʌðɚ', 'grandfather': 'ˈgrænfɑːðɚ',
    'thirteen': 'ˌθɜːrˈtiːn', 'fourteen': 'ˌfɔːrˈtiːn', 'fifteen': 'ˌfɪfˈtiːn',
    'sixteen': 'ˌsɪksˈtiːn', 'seventeen': 'ˌsevənˈtiːn', 'eighteen': 'ˌeɪˈtiːn',
    'nineteen': 'ˌnaɪnˈtiːn', 'thirty': 'ˈθɜːrti', 'forty': 'ˈfɔːrti', 'fifty': 'ˈfɪfti',
    'hundred': 'ˈhʌndrəd', 'breakfast': 'ˈbrekfəst', 'homework': 'ˈhoʊmwɜːrk',
    'birthday': 'ˈbɜːrθdeɪ', 'holiday': 'ˈhɑːlədeɪ', 'weekend': 'ˈwiːkend',
    'football': 'ˈfʊtbɔːl', 'basketball': 'ˈbæskɪtbɔːl', 'strawberry': 'ˈstrɔːberi',
    'pineapple': 'ˈpaɪnæpl', 'banana': 'bəˈnænə', 'potato': 'pəˈteɪtoʊ',
    'chocolate': 'ˈtʃɑːklət', 'sandwich': 'ˈsænwɪtʃ', 'vegetable': 'ˈvedʒtəbl',
    'restaurant': 'ˈrestərɑːnt', 'supermarket': 'ˈsuːpɚmɑːrkɪt', 'hospital': 'ˈhɑːspɪtl',
    'cinema': 'ˈsɪnəmə', 'museum': 'ˈmjuːziəm', 'apartment': 'əˈpɑːrtmənt',
    'tv': 'ˈtiː ˌviː', 'outside': 'ˌaʊtˈsaɪd', 'downstairs': 'ˌdaʊnˈsterz',
    'question': 'ˈkwestʃən', 'uniform': 'ˈjuːnɪfɔːrm', 'upstairs': 'ˌʌpˈsterz',
}


def isv(t):
    return t.rstrip('012') in VOW


def lvl(t):
    m = re.search(r'(\d)$', t)
    return int(m.group(1)) if m else 0


def onset_split(cons):
    s = ''.join(cons)
    if not cons:
        return 0
    if len(cons) >= 3 and s[-3:] in LEGAL3:
        return 3
    if len(cons) >= 2 and s[-2:] in LEGAL2:
        return 2
    if len(cons) >= 2 and s[-1] in ('j', 'w', 'r', 'l'):
        return 2
    return 1


def conv(w0):
    w = w0.lower()
    if w in OVERRIDE:
        return OVERRIDE[w]
    cands = D.get(w) or D.get(w.replace(' ', '') + '')
    if not cands:
        return ''
    ph = cands[0]
    toks = [(t.rstrip('012'), lvl(t), isv(t)) for t in ph]
    n = len(toks)
    res = ''
    pending = []
    i = 0
    while i < n:
        base, st, isvowel = toks[i]
        if not isvowel:
            pending.append(CONS.get(base, base.lower()))
            i += 1
            continue
        # 下一个音素是 R，且 R 后面还有元音 → R 作下一音节声母，否则并入元音
        nxt = toks[i + 1] if i + 1 < n else None
        nxt2 = toks[i + 2] if i + 2 < n else None
        r_coda = bool(nxt and nxt[0] == 'R' and not (nxt2 and nxt2[2] and nxt2[0] != 'R'))

        # 声母分配
        if pending:
            if i + 1 < n:
                k = onset_split(pending)
            else:
                k = len(pending)
            coda_cnt = len(pending) - k
        else:
            k = 0
            coda_cnt = 0
        onset = ''.join(pending[coda_cnt:])
        coda = ''.join(pending[:coda_cnt])
        pending = []

        if base == 'AA':
            v = 'ɑː'
        elif base == 'AE':
            v = 'æ'
        elif base == 'AH':
            if st == 0 and i + 1 < n and toks[i + 1][0] in ('L', 'N') and not (i + 2 < n and toks[i + 2][2]):
                v = ''
            else:
                v = 'ʌ' if st > 0 else 'ə'
        elif base == 'AO':
            v = 'ɑː'
        elif base == 'AW':
            v = 'aʊ'
        elif base == 'AY':
            v = 'aɪ'
        elif base == 'EH':
            v = 'e'
        elif base == 'ER':
            v = 'ɝː' if st > 0 else 'ɚ'
        elif base == 'EY':
            v = 'eɪ'
        elif base == 'IH':
            v = 'ɪ'
        elif base == 'IY':
            v = 'iː'
        elif base == 'OW':
            v = 'oʊ'
        elif base == 'OY':
            v = 'ɔɪ'
        elif base == 'UH':
            v = 'ʊ'
        elif base == 'UW':
            v = 'uː'
        else:
            v = base.lower()

        if r_coda and base not in ('ER',):
            v = v + 'r'
            i += 2
        else:
            i += 1

        mark = 'ˈ' if st == 1 else ('ˌ' if st == 2 else '')
        res += coda + mark + onset + v

    # 结尾残留辅音
    res += ''.join(pending)
    # 单音节词不标重音
    if sum(1 for t in toks if t[2]) <= 1:
        res = res.replace('ˈ', '').replace('ˌ', '')
    return res


def main():
    u = json.load(io.open(P, encoding='utf-8'))
    miss = []
    for x in u:
        for w in x['words']:
            en = w['en']
            ipa = conv(en)
            if not ipa:
                miss.append(en)
                ipa = w.get('ipa', '').strip('/')
            w['ipaUs'] = '/' + ipa + '/'
    json.dump(u, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('美式音标写入', sum(len(x['words']) for x in u), '词')
    if miss:
        print('词典缺失', len(miss), miss)


if __name__ == '__main__':
    main()
