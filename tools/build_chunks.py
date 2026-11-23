# -*- coding: utf-8 -*-
"""把单词页例句切成「意群块」，每块配一句短中文，前端按住/点按显示。
用法: python3 tools/build_chunks.py            # 生成 data/chunks.json 供预览
      python3 tools/build_chunks.py --apply    # 写回 chapters.json 的 word['chunks']
"""
import json, io, re, sys

P = 'data/chapters.json'

DET = {'the','a','an','this','that','these','those','my','your','his','her','our','its',
       'one','two','three','four','five','six','seven','eight','nine','ten','many','some',
       'eleven','twelve','thirteen','fourteen','fifteen','sixteen','seventeen','eighteen',
       'nineteen','twenty','thirty','forty','fifty','hundred'}
PREP = {'in','on','at','near','under','behind','beside','above','below','around','along',
        'across','over','with','for','to','from','of','between'}
BE = {'is','am','are'}
NAMES = {'tom':'汤姆','lily':'莉莉','sam':'萨姆','amy':'艾米','bob':'鲍勃','ben':'本',
         'lucy':'露西','mimi':'咪咪','mum':'妈妈','dad':'爸爸','mummy':'妈妈','daddy':'爸爸',
         'teacher':'老师'}
FUNC = {
 'this':'这','that':'那','these':'这些','those':'那些','it':'它','mrs':'女士','mr':'先生',
 'i':'我','you':'你','we':'我们','he':'他','she':'她','it':'它','they':'他们','me':'我',
 'us':'我们','him':'他','them':'他们','mine':'我的',
 'is':'是','am':'是','are':'是','be':'是','was':'是','were':'是',
 'not':'不','no':'不','yes':'好的','please':'请','thanks':'谢谢','thank':'谢谢',
 'can':'会','do':'做','does':'做','let':'让',
 'and':'和','or':'还是','but':'但是','so':'这么','very':'很','too':'也','again':'再',
 'here':'这儿','there':'那儿','now':'现在','up':'起来','down':'下去',
 'what':'什么','how':'怎样','who':'谁','where':'哪儿','whose':'谁的','which':'哪个',
 'look':'看','see':'看见','say':'说','come':'来','go':'去','have':'有','has':'有',
 'hello':'你好','hi':'嗨','bye':'再见','good':'好','morning':'早上','afternoon':'下午',
 'evening':'晚上','night':'夜里','today':'今天','tomorrow':'明天',
}
NUM_CN = {'one':'一','two':'两','three':'三','four':'四','five':'五','six':'六',
          'seven':'七','eight':'八','nine':'九','ten':'十','many':'很多','some':'一些',
          'eleven':'十一','twelve':'十二','thirteen':'十三','fourteen':'十四','fifteen':'十五',
          'sixteen':'十六','seventeen':'十七','eighteen':'十八','nineteen':'十九','twenty':'二十',
          'thirty':'三十','forty':'四十','fifty':'五十','hundred':'百'}
MID = {'left':'左','right':'右'}
DET_CN = {'the':'','a':'','an':'','this':'这','that':'那','these':'这些','those':'那些',
          'my':'我的','your':'你的','his':'他的','her':'她的','our':'我们的','its':'它的'}
# 量词：按名词归类，缺省「个」
MW = {
 'tiger':'只','lion':'只','monkey':'只','elephant':'头','giraffe':'只','bear':'只','wolf':'只',
 'fox':'只','deer':'只','snake':'条','turtle':'只','kangaroo':'只','koala':'只','penguin':'只',
 'cat':'只','dog':'只','bird':'只','duck':'只','pig':'只','cow':'头','sheep':'只','rabbit':'只',
 'panda':'只','hen':'只','chick':'只','horse':'匹','goat':'只','goose':'只','mouse':'只',
 'frog':'只','bee':'只','butterfly':'只','ladybug':'只','crab':'只','shark':'条','whale':'头',
 'dolphin':'条','octopus':'只','snail':'只','ant':'只','spider':'只','worm':'条','starfish':'只',
 'fish':'条','ball':'个','balloon':'个','kite':'只','doll':'个','robot':'个','block':'块',
 'teddy':'个','puzzle':'副','bubble':'个','drum':'面','toy':'个','gift':'份','candle':'根',
 'card':'张','ribbon':'条','pumpkin':'个','lantern':'盏','firework':'个','mask':'个',
 'apple':'个','banana':'根','egg':'个','cake':'块','cookie':'块','pizza':'张','carrot':'根',
 'tomato':'个','potato':'个','grape':'颗','pear':'个','peach':'个','melon':'个','lemon':'个',
 'strawberry':'颗','cherry':'颗','mango':'个','onion':'个','corn':'根','nut':'颗',
 'watermelon':'个','pineapple':'个','coconut':'个','blueberry':'颗','kiwi':'个','avocado':'个',
 'plum':'个','apricot':'个','sandwich':'个','hamburger':'个','chip':'片','candy':'颗',
 'tree':'棵','flower':'朵','leaf':'片','seed':'颗','rock':'块','stone':'块','stick':'根',
 'star':'颗','moon':'个','sun':'个','cloud':'朵','rainbow':'道',
 'bus':'辆','car':'辆','train':'列','plane':'架','boat':'条','bike':'辆','taxi':'辆',
 'truck':'辆','ship':'艘','subway':'趟','tractor':'台',
 'book':'本','notebook':'本','storybook':'本','pen':'支','pencil':'支','ruler':'把','key':'把',
 'umbrella':'把','bag':'个','schoolbag':'个','cup':'个','bottle':'个','plate':'个','bowl':'个',
 'fork':'把','knife':'把','spoon':'把','teapot':'个','clock':'个','lamp':'盏','sofa':'张',
 'chair':'把','table':'张','bed':'张','door':'扇','window':'扇','map':'张','picture':'张',
 'board':'块','phone':'部','computer':'台','fan':'个','curtain':'块','towel':'条','blanket':'条',
 'pillow':'个','soap':'块','toothbrush':'把','sock':'只','shoe':'只','glove':'只','scarf':'条',
 'hat':'顶','shirt':'件','coat':'件','dress':'条','skirt':'条','sweater':'件','jacket':'件',
 'trouser':'条','uniform':'套','glasses':'副','shoe':'双',
 'eye':'只','ear':'只','hand':'只','foot':'只','tooth':'颗','leg':'条','arm':'条',
 'finger':'根','knee':'个','shoulder':'个','neck':'个','back':'个','stomach':'个','elbow':'个',
 'wrist':'个','ankle':'个','toe':'个','thumb':'个','chest':'个','lesson':'节','class':'节',
 'story':'个','dream':'个','costume':'套','treat':'颗','fish':'条',
 'sky':'片','night':'个','sugar':'种',
 'house':'座','home':'个','room':'间','bedroom':'间','kitchen':'间','bathroom':'间','garden':'个',
 'balcony':'个','school':'所','classroom':'间','library':'个','gym':'个','lab':'间','hall':'个',
 'canteen':'个','gate':'扇','path':'条','playground':'个','bench':'张','fountain':'个',
 'shop':'家','hospital':'家','office':'间','company':'家','zoo':'个','farm':'个','field':'块',
 'barn':'间','fence':'道','bridge':'座','river':'条','lake':'个','hill':'座','mountain':'座',
 'valley':'个','cave':'个','island':'座','beach':'片','desert':'片','forest':'片','wave':'个',
 'building':'栋','city':'座','apartment':'套','house':'座',
 'story':'个','dream':'个','song':'首','game':'个','movie':'部','video':'段','comic':'本',
 'cartoon':'部','sticker':'张','marble':'颗','puppet':'个','dice':'颗',
 'sock':'只','boot':'双','tie':'条','belt':'条','ring':'枚','watch':'块',
}
ADJ_CN = {'sunny':'晴朗','rainy':'下雨','windy':'刮风','snowy':'下雪','cloudy':'多云',
          'foggy':'有雾','humid':'潮湿','dry':'干','wet':'湿','delicious':'好吃','ready':'准备好',
          'tidy':'整洁','lost':'丢了','open':'开着','hard':'难','fun':'好玩','messy':'乱',
          'slow':'慢','fast':'快','strange':'奇怪',
          'left':'左','right':'右','red':'红','blue':'蓝','green':'绿','yellow':'黄','black':'黑','white':'白',
          'brown':'棕','orange':'橙','grey':'灰','gray':'灰','pink':'粉','purple':'紫',
          'gold':'金','silver':'银','new':'新','old':'旧','big':'大','small':'小','long':'长',
          'short':'短','tall':'高','thin':'瘦','fat':'胖','hot':'热','cold':'冷','warm':'暖',
          'cool':'凉','nice':'好','clean':'干净','dirty':'脏','happy':'开心','sad':'难过',
          'funny':'逗','kind':'善良','clever':'聪明','friendly':'友好','heavy':'重','empty':'空',
          'full':'满','quiet':'安静','bright':'亮','dark':'暗','ripe':'熟','fresh':'新鲜',
          'sour':'酸','cheap':'便宜','expensive':'贵','best':'最好的','strong':'壮','hungry':'饿',
          'sleepy':'困','tired':'累','scared':'害怕','angry':'生气','excited':'兴奋','lucky':'幸运'}
NOUN_CN = {'orange':'橙子','sweet':'糖','light':'灯','orange':'橙子','glass':'玻璃杯',
           'water':'水','fish':'鱼','chicken':'鸡肉','tea':'茶','juice':'果汁'}
PHRASES = {
 'welcome to':'欢迎来到','welcome back':'欢迎回来','be quiet':'安静点','be careful':'小心',
 'good day':'美好的一天','rest day':'休息日','page one':'第一页','page two':'第二页',
 'one minute':'一分钟','one hour':'一小时','half past one':'一点半','half past two':'两点半',
 'a cup of':'一杯','a glass of':'一杯','a bottle of':'一瓶','a slice of':'一片',
 'a bunch of':'一串','a quarter of':'四分之一','a bowl of':'一碗','a plate of':'一盘',
 'one hundred':'一百','a hundred':'一百','in front':'在前面','at school':'在学校',
 'this is':'这是','that is':'那是','these are':'这些是','it is':'它是','there is':'有',
 'i am':'我是','we are':'我们是','they are':'他们是','you are':'你是','he is':'他是','she is':'她是',
 'look at':'看','look out':'小心','come here':'过来','come in':'进来','go home':'回家',
 'go to school':'去上学','go to bed':'去睡觉','get up':'起床','wake up':'醒一醒',
 'sit down':'坐下','stand up':'站起来','put on':'穿上','take off':'脱下','come on':'来吧',
 'a lot of':'很多','lots of':'很多','how many':'多少个','how old':'多大','what color':'什么颜色',
 'thank you':'谢谢你','good morning':'早上好','good afternoon':'下午好','good evening':'晚上好',
 'good night':'晚安','nice to meet you':'很高兴认识你','see you':'再见','excuse me':'打扰一下',
 'come back':'回来','have fun':'玩得开心','be careful':'小心','too much':'太多',
 'at home':'在家','at school':'在学校','in the morning':'早上','in the afternoon':'下午',
 'in the evening':'晚上','at night':'夜里','every day':'每天','all day':'一整天',
 'this way':'这边走','over there':'在那边','right now':'现在','at last':'最后',
 'my name':'我的名字','your name':'你的名字',
}
PHRASES.update({'in the middle':'在中间','on the top':'在顶上','at the bottom':'在底部',
                'up the hill':'上山','down the hill':'下山','a rest day':'一个休息日',
                'a treat':'请客','in the morning':'早上',
                'on sale':'打折','pay for':'付钱买','a good day':'美好的一天',
                'hurry up':'快一点','have a break':'休息一下','have dinner':'吃晚饭',
                'have lunch':'吃午饭','have breakfast':'吃早饭','a mess':'乱成一团',
                'best friend':'最好的朋友','good friend':'好朋友','move to':'搬去',
                'ten degrees':'十度','a second':'一秒',
                'have a bath':'洗澡','have a shower':'洗澡','at the stove':'在炉子旁',
                'in that corner':'在那个角落','in this corner':'在这个角落',
                'i am':'我','we are':'我们','they are':'他们','you are':'你','he is':'他',
                'she is':'她','a good day':'美好的一天','a bad day':'糟糕的一天',
                'left hand':'左手','right hand':'右手','left foot':'左脚','right foot':'右脚',
                'left eye':'左眼','right eye':'右眼','one week':'一个星期','half a cake':'半块蛋糕'})
OVERRIDE = {}   # "整句" -> [[en,cn],...] 人工兜底


def first_cn(cn):
    s = re.sub(r'[（(][^）)]*[）)]', '', str(cn or ''))
    s = re.split(r'[；;，,。/]', s)[0].strip()
    return s


def look(tok, words):
    k = tok.lower().strip('.,!?')
    if k in words: return k
    for cand in (k[:-1], k[:-2], re.sub(r'ies$','y',k), re.sub(r'es$','',k)):
        if cand in words: return cand
    return None


def gloss(tok, words):
    k = tok.lower().strip('.,!?')
    if k in NAMES: return NAMES[k]
    if k in FUNC: return FUNC[k]
    if k in NUM_CN: return NUM_CN[k]
    hit = look(k, words)
    if hit: return first_cn(words[hit]['cn'])
    return ''


def is_det(t): return t.lower().strip('.,!?') in DET


def det_chunk(tokens, words):
    """限定词打头的名词短语 → 一块：那只大老虎 / 我的新学校"""
    head = tokens[0].lower().strip('.,!?')
    body = [t for t in tokens[1:] if t.lower().strip('.,!?') not in DET_CN]
    if not body:
        return None
    parts = [gloss(t, words) for t in body]
    if any(not p for p in parts):
        return None
    noun_tok = body[-1].lower().strip('.,!?')
    noun = look(noun_tok, words) or noun_tok
    # 形容词串：只取名词前面的，中间夹 and 的合并成「黑白相间」
    adj_parts = [ADJ_CN.get(t.lower().strip('.,!?'), p) for t, p in zip(body[:-1], parts[:-1])]
    adj_cn = ''
    if adj_parts:
        adj_parts = [ADJ_CN.get(t.lower().strip('.,!?'), p) for t, p in zip(body[:-1], adj_parts)]
        if any(t.lower().strip('.,!?') == 'and' for t in body[:-1]) and len(adj_parts) >= 2:
            real = [p for t, p in zip(body[:-1], adj_parts) if t.lower() != 'and']
            land = [p for t, p in zip(body[:-1], adj_parts) if t.lower() != 'and']
            adj_cn = ''.join(land) + '相间的'
            if len(adj_cn) > 6:
                adj_cn = ''.join(land)
        else:
            adj_cn = ''.join(adj_parts)
    noun_cn = NOUN_CN.get(noun, parts[-1])
    mw = MW.get(noun, '') or '个'
    cn = DET_CN.get(head, '') or NUM_CN.get(head, '')
    if head in ('a', 'an'):
        full = '一' + mw + adj_cn + noun_cn
    elif head in NUM_CN:
        full = cn + mw + adj_cn + noun_cn
    elif head in ('this','that','these','those'):
        full = cn + mw + adj_cn + noun_cn
    else:
        full = cn + adj_cn + noun_cn
    return full


VERBS = {'go','come','run','jump','swim','sit','stand','walk','sleep','eat','drink','wash',
         'brush','open','close','give','take','look','listen','clap','cry','laugh','smile','hug',
         'see','hear','smell','taste','touch','climb','kick','throw','catch','push','find','borrow',
         'return','wear','guess','sing','dance','paint','draw','play','share','keep','move','wake',
         'rush','rest','break','finish','cut','order','help','cook','drive','visit','show','carry',
         'load','try','fit','pay','change','mix','dye','plant','pick','feed','dig','harvest','grow',
         'invite','wish','celebrate','decorate','bake','fry','roast','count','win','lose','greet',
         'study','learn','meet','jumps','fits','grows'}
STOP_TAIL = {'please','thanks','too','now','again','here','there','today','tomorrow','soon'}
POS = {'between':'中间','behind':'后面','beside':'旁边','above':'上面','below':'下面',
       'under':'下面','over':'上方','around':'周围','along':'沿着','across':'穿过',
       'near':'附近','inside':'里面','outside':'外面','in':'里','on':'上','at':''}
PREP_PLAIN = {'to':'去','for':'给','from':'从','of':'的','with':'和','at':'在'}


PLACE_NO_RI = {'school','classroom','canteen','hall','garden','park','zoo','farm',
               'home','library','gym','class','office','hospital','company','city'}


TIME_NOUN = {'hour','minute','day','week','month','year','night'}


DATE_NO = {'january','february','march','april','may','june','july','august','september',
           'october','november','december','monday','tuesday','wednesday','thursday','friday',
           'saturday','sunday','spring','summer','autumn','winter','morning','afternoon','evening',
           'night','today','tomorrow','monday'}


def _prep_cn(prep, obj_cn, obj_key=''):
    if obj_key in DATE_NO:
        return '在' + obj_cn
    if prep == 'for' and obj_key in TIME_NOUN:
        return obj_cn
    if prep == 'on':
        return '在' + obj_cn + '上'
    if prep == 'in':
        return '在' + obj_cn + ('' if obj_key in PLACE_NO_RI else '里')
    if prep in ('near', 'inside', 'outside'):
        return '在' + obj_cn + {'near': '附近', 'inside': '里', 'outside': '外面'}[prep]
    if prep == 'along':
        return '沿着' + obj_cn
    if prep == 'across':
        return '穿过' + obj_cn
    if prep in POS:
        return '在' + obj_cn + POS[prep]
    return PREP_PLAIN.get(prep, prep) + obj_cn


def _clause(toks, words):
    chunks = []
    i = 0
    n_all = len(toks)
    while i < n_all:
        # 1) 短语表最长匹配
        got = None
        for n in (4, 3, 2, 1):
            if i + n <= n_all:
                key = ' '.join(t.lower().strip('.,!?') for t in toks[i:i + n])
                if key in PHRASES:
                    got = (n, PHRASES[key]); break
        if got:
            n, cn = got
            chunks.append([' '.join(toks[i:i + n]), cn]); i += n; continue
        # 2) 限定词名词短语
        if is_det(toks[i]):
            n = 1
            while i + n < n_all:
                t = toks[i + n].lower().strip('.,!?')
                if t in STOP_TAIL: break
                if t == 'and':
                    prev = toks[i + n - 1].lower().strip('.,!?')
                    nxt = toks[i + n + 1].lower().strip('.,!?') if i + n + 1 < n_all else ''
                    if prev in ADJ_CN and (nxt in ADJ_CN):
                        n += 1
                    else:
                        break
                elif t in VERBS or t in PREP:
                    break
                elif look(toks[i + n], words) is not None or t in MID:
                    prev_noun = (look(toks[i + n - 1], words)
                                 and toks[i + n - 1].lower().strip('.,!?') not in ADJ_CN
                                 and toks[i + n - 1].lower().strip('.,!?') not in NUM_CN
                                 and toks[i + n - 1].lower().strip('.,!?') not in DET)
                    if t in ADJ_CN and prev_noun:
                        break
                    n += 1
                else:
                    break
            cn = det_chunk(toks[i:i + n], words)
            if cn:
                chunks.append([' '.join(toks[i:i + n]), cn]); i += n; continue
        # 3) 介词短语
        if toks[i].lower() in ('on', 'off') and (i + 1 >= n_all or toks[i + 1].lower().strip('.,!?') in STOP_TAIL):
            chunks.append([toks[i], '开着' if toks[i].lower() == 'on' else '关着']); i += 1; continue
        if toks[i].lower() in PREP and i + 1 < n_all:
            prep = toks[i].lower()
            n = 1
            if toks[i + 1].lower().strip('.,!?') in DET | {'my','your','his','her','our'}:
                n = 2
                while i + n < n_all:
                    t = toks[i + n].lower().strip('.,!?')
                    if t in STOP_TAIL: break
                    if look(toks[i + n], words) is not None or t in MID:
                        n += 1
                    else:
                        break
            else:
                n = 2
            obj_tokens = toks[i + 1:i + n]
            obj_cn = ''
            hit = look(obj_tokens[-1], words) or obj_tokens[-1].lower().strip('.,!?')
            if hit in words:
                obj_cn = NOUN_CN.get(hit, first_cn(words[hit]['cn']))
            elif hit in NAMES:
                obj_cn = NAMES[hit]
            else:
                obj_cn = DET_CN.get(obj_tokens[0].lower().strip('.,!?'), '') + gloss(obj_tokens[-1], words)
            if obj_cn:
                chunks.append([' '.join(toks[i:i + n]),
                               _prep_cn(prep, obj_cn, hit if hit in words else '')])
                i += n; continue
        # 4) very / so + 形容词 → 一块：很干净
        k = toks[i].lower().strip('.,!?')
        if k in ('very', 'so') and i + 1 < n_all:
            nk = toks[i + 1].lower().strip('.,!?')
            ac = ADJ_CN.get(nk)
            if ac:
                chunks.append([' '.join(toks[i:i + 2]), ('很' if k == 'very' else '这么') + ac])
                i += 2; continue
        # 5) 单词
        chunks.append([toks[i], gloss(toks[i], words)]); i += 1
    return chunks


def split_sentence(en, words):
    body = en.strip()
    end = ''
    while body and body[-1] in '.!?':
        end = body[-1] + end; body = body[:-1]
    aux = ''
    if end == '?' and body and body.split()[0].lower() in ('is', 'are', 'can', 'do', 'does', 'am'):
        aux = body.split()[0]
        body = ' '.join(body.split()[1:])
    res = []
    for ci, clause in enumerate(re.split(r',\s*', body)):
        toks = [t for t in clause.split() if t]
        if not toks: continue
        cs = _clause(toks, words)
        if ci:
            cs[0][0] = ', ' + cs[0][0] if False else cs[0][0]
        res += cs
    fixed = []
    for c in res:
        if fixed and fixed[-1][1] == '':
            fixed[-1] = [fixed[-1][0] + ' ' + c[0], c[1]]
        elif c[1] == '':
            fixed.append([c[0], ''])
        else:
            fixed.append(c)
    res = [c for c in fixed if c[1]]
    # 把孤立的 is/are/am 并入后一块，避免「is=是」这种单块
    BARE_ADJ = {'好','大','小','新','旧','长','短','高','矮','快','慢','热','冷','干净',
                '漂亮','可爱','聪明','开心','忙','累','难','容易','甜','好吃','红','蓝','绿'}
    merged = []
    for c in res:
        if merged and merged[-1][1] == '是' and c[1]:
            if c[1].startswith('很') or c[1].startswith('这么') or c[1].startswith('非常'):
                cn = c[1]
            elif c[1] in BARE_ADJ:
                cn = '很' + c[1]
            else:
                cn = '是' + c[1]
            merged[-1] = [merged[-1][0] + ' ' + c[0], cn]
        else:
            merged.append(c)
    res = merged
    if aux:
        res.insert(0, [aux, ''])
    if end and res:
        if end == '?':
            res[-1][1] = res[-1][1] + '吗？'
            res[-1][0] = res[-1][0] + '?'
        else:
            res[-1][0] = res[-1][0] + end
    return res


def main():
    u = json.load(io.open(P, encoding='utf-8'))
    words = {w['en'].lower(): w for x in u for w in x['words']}
    out = {}
    for x in u:
        for w in x['words']:
            en = w['sentence']
            if not en: continue
            if en in OVERRIDE:
                out[(x['id'], w['en'])] = OVERRIDE[en]
            else:
                out[(x['id'], w['en'])] = split_sentence(en, words)
    apply = '--apply' in sys.argv
    if apply:
        for x in u:
            for w in x['words']:
                c = out.get((x['id'], w['en']))
                if c: w['chunks'] = [{'en': a, 'cn': b} for a, b in c]
                for st in (w.get('sentences') or []):
                    if st.get('en'):
                        cc = OVERRIDE.get(st['en']) or split_sentence(st['en'], words)
                        st['chunks'] = [{'en': a, 'cn': b} for a, b in cc]
        json.dump(u, io.open(P, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print('写入 chunks', len(out), '句')
        return
    lines = []
    for x in u:
        for w in x['words']:
            c = out[(x['id'], w['en'])]
            lines.append('%s\t%s\t%s' % (w['en'], w['sentence'],
                                         ' | '.join('%s=%s' % (a, b) for a, b in c)))
    io.open('data/chunks_preview.txt', 'w', encoding='utf-8').write('\n'.join(lines) + '\n')
    print('生成', len(lines), '句 → data/chunks_preview.txt')


if __name__ == '__main__':
    main()
