# -*- coding: utf-8 -*-
"""L1 交叉页段落（第一人称叙述体，Lily 自述，无对白）。

结构：
PASSAGES = {
  "unit31": [
     {"title": "我是新来的", "scene": "...", "lines": [("en", "cn"), ...]},
     ...（每课 3 段）
  ]
}

写法（六条）：
1. 不写对白、不标说话人，Lily 第一人称连续讲述。
2. 每课 3 段 = 同一场景，开始—进行—结束。
3. 每段 3–5 句，句句承接。
4. 每段只聚焦 2–4 个本课词，旧词负责串场景。
5. 除最后一句「你」的互动问句外，不提问不喊话。
6. 中文像妈妈在旁边说的话，意译不直译。

校验：python3 tools/passage_check.py
"""

PASSAGES = {
    # ==================== 第 01 课 问候与认识 ====================
    "unit31": [
        {"title": "我是新来的", "scene": "开学第一天，站在教室门口", "lines": [
            ("Hello! My name is Lily.", "大家好！我叫莉莉。"),
            ("I am a new student.", "我是新来的同学。"),
            ("This is my new school.", "这就是我的新学校。"),
            ("It is very big.", "学校特别大。"),
            ("I love my new school!", "我可喜欢它啦！"),
        ]},
        {"title": "我的老师和同学", "scene": "老师走过来，介绍新同学", "lines": [
            ("She is my teacher.", "这是我的老师。"),
            ("My teacher is very nice.", "她人特别好。"),
            ("This is Tom.", "这是汤姆。"),
            ("He is my classmate.", "他是我的同学。"),
            ("Nice to meet you, Tom!", "很高兴认识你，汤姆！"),
        ]},
        {"title": "第一节英语课", "scene": "上课铃响，开始学歌", "lines": [
            ("This is a new lesson.", "新课开始了。"),
            ("We learn a song.", "我们要学一首歌。"),
            ("The song is very nice.", "这首歌特别好听。"),
            ("I can sing a new song now.", "我现在会唱一首新歌了。"),
        ]},
    ],
    # ==================== 第 02 课 教室 ====================
    "unit32": [
        {"title": "走进新教室", "scene": "推门进教室", "lines": [
            ("This is our new classroom.", "这是我们的新教室。"),
            ("It is very big.", "特别大。"),
            ("Look at the big board!", "快看这块大黑板！"),
            ("The board is black.", "黑板是黑色的。"),
        ]},
        {"title": "我的座位", "scene": "走到自己的座位坐下", "lines": [
            ("My desk is very clean.", "我的书桌很干净。"),
            ("My seat is in that corner.", "我的座位就在那个角落。"),
            ("The map is on the wall.", "地图挂在墙上。"),
            ("It is very white.", "墙特别白。"),
        ]},
        {"title": "快下课了", "scene": "看钟、天黑、回家", "lines": [
            ("A clock is on the wall.", "墙上有个钟。"),
            ("The light is on.", "灯还亮着。"),
            ("The sun is down.", "六点了，太阳都落山了。"),
            ("I go home now.", "我该回家啦。"),
            ("See you tomorrow!", "明天见！"),
        ]},
    ],
    # ==================== 第 03 课 我的书包 ====================
    "unit33": [
        {"title": "书包好重", "scene": "早上背起书包出门", "lines": [
            ("My schoolbag is very heavy.", "我的书包特别重。"),
            ("My English and maths are in it.", "英语和数学都在里面。"),
            ("I am so tired!", "我累坏啦！"),
        ]},
        {"title": "钥匙丢了", "scene": "翻书包找钥匙", "lines": [
            ("My key is lost.", "我的钥匙丢了。"),
            ("I look in my schoolbag.", "我在书包里翻。"),
            ("I find my key!", "找到了！"),
            ("It is here!", "原来在这儿！"),
        ]},
        {"title": "借故事书", "scene": "借书、看书、还书", "lines": [
            ("I borrow a storybook.", "我借了一本故事书。"),
            ("I love the story.", "这个故事我特别喜欢。"),
            ("I look at page one.", "我先看第一页。"),
            ("I return it now.", "看完就还回去。"),
        ]},
    ],
    # ==================== 第 04 课 我的朋友 ====================
    "unit34": [
        {"title": "我的好朋友", "scene": "介绍同桌 Tom", "lines": [
            ("Tom is my best friend.", "汤姆是我最好的朋友。"),
            ("He is very tall.", "他个子特别高。"),
            ("He is very strong.", "还特别壮。"),
            ("He is friendly.", "对人特别友好。"),
        ]},
        {"title": "猜猜是谁", "scene": "让小朋友猜同学", "lines": [
            ("Guess my friend!", "猜猜是哪个朋友！"),
            ("He is very clever.", "他特别聪明。"),
            ("He wears glasses.", "还戴着眼镜。"),
            ("He is very quiet.", "平时很安静。"),
        ]},
        {"title": "一起玩", "scene": "操场上一起跑", "lines": [
            ("We run together.", "我们总是一起跑。"),
            ("He is very funny.", "他特别好玩。"),
            ("He is kind to me.", "对我特别好。"),
            ("I love my best friend.", "我最喜欢这个好朋友啦。"),
        ]},
    ],
    # ==================== 第 05 课 我的家 ====================
    "unit35": [
        {"title": "我的家", "scene": "搬进新家，上楼看卧室", "lines": [
            ("This is our new apartment.", "这是我们的新公寓。"),
            ("My bedroom is upstairs.", "我的卧室在楼上。"),
            ("It is very tidy.", "收拾得特别整洁。"),
        ]},
        {"title": "楼下厨房", "scene": "跑到楼下，妈妈在做饭", "lines": [
            ("My kitchen is downstairs.", "厨房在楼下。"),
            ("The bathroom is here.", "浴室也在这儿。"),
            ("Mum is in the kitchen now.", "妈妈正在厨房忙。"),
        ]},
        {"title": "阳台和邻居", "scene": "阳台上分蛋糕", "lines": [
            ("We sit on the balcony.", "我们坐在阳台上。"),
            ("My neighbour is in the garden.", "邻居在花园里。"),
            ("We share a big cake!", "我们一起分了个大蛋糕！"),
        ]},
    ],
    # ==================== 第 06 课 晚餐与三餐 ====================
    "unit36": [
        {"title": "早饭好了", "scene": "早上帮妈妈端早饭", "lines": [
            ("Breakfast is ready.", "早饭做好啦。"),
            ("I help my mum.", "我帮妈妈端东西。"),
            ("I have bread and milk.", "我吃面包喝牛奶。"),
        ]},
        {"title": "学校午饭", "scene": "中午在食堂吃饭", "lines": [
            ("We have lunch at school.", "我们在学校吃午饭。"),
            ("I have vegetables and soup.", "我吃蔬菜，还喝汤。"),
            ("It is very good.", "味道特别好。"),
        ]},
        {"title": "晚饭上桌", "scene": "晚上有肉有菜", "lines": [
            ("Dinner is ready.", "晚饭好啦。"),
            ("We have beef and chicken.", "今天有牛肉和鸡肉。"),
            ("It is very delicious!", "太好吃啦！"),
        ]},
    ],
    # ==================== 第 07 课 家人与职业 ====================
    "unit37": [
        {"title": "爸爸上班", "scene": "爸爸出门去公司", "lines": [
            ("My dad is in the office.", "爸爸在办公室。"),
            ("He loves this job.", "他特别喜欢这份工作。"),
            ("He can drive a car.", "他还会开车。"),
        ]},
        {"title": "妈妈在医院", "scene": "妈妈还没回家", "lines": [
            ("My mum is not here.", "妈妈不在家。"),
            ("She is in the hospital.", "她在医院。"),
            ("Her job is very hard.", "她的工作特别辛苦。"),
        ]},
        {"title": "我们一家人", "scene": "全家坐在一起", "lines": [
            ("We are a team.", "我们一家人像一个小团队。"),
            ("My parents are here.", "爸爸妈妈都在。"),
            ("I am the daughter.", "我是女儿。"),
            ("My brother is the son.", "弟弟是儿子。"),
        ]},
    ],
    # ==================== 第 08 课 学校设施 ====================
    "unit38": [
        {"title": "走进校门", "scene": "早上从大门走到教室", "lines": [
            ("The gate is open.", "大门开着。"),
            ("This path is very long.", "这条小路特别长。"),
            ("This is the way to my class.", "顺着这条路就到我们班。"),
        ]},
        {"title": "参观图书馆", "scene": "老师带大家参观", "lines": [
            ("We visit the library.", "我们去参观图书馆。"),
            ("It is very quiet.", "里面特别安静。"),
            ("The hall is here.", "礼堂在这儿。"),
        ]},
        {"title": "食堂和操场", "scene": "中午吃饭、饭后去玩", "lines": [
            ("The canteen is very full.", "食堂里挤满了人。"),
            ("We eat and run.", "我们吃完饭就跑出去玩。"),
            ("The playground is empty now.", "现在操场都空了。"),
        ]},
    ],
    # ==================== 第 09 课 时间与作息 ====================
    "unit39": [
        {"title": "闹钟响了", "scene": "早上闹钟叫醒", "lines": [
            ("My alarm is on.", "闹钟响了。"),
            ("I wake up.", "我醒了。"),
            ("I am early today.", "今天起得早。"),
            ("No hurry!", "一点都不着急！"),
        ]},
        {"title": "赶去学校", "scene": "跑着去学校", "lines": [
            ("I rush to school.", "我赶快跑去学校。"),
            ("I can not be late.", "可不能迟到。"),
            ("One minute, please!", "等我一下呀！"),
        ]},
        {"title": "下课休息", "scene": "一点半下课", "lines": [
            ("It is half past one.", "现在一点半。"),
            ("We have a break.", "我们下课休息。"),
            ("It is an hour long.", "能歇整整一个钟头呢。"),
        ]},
    ],
    # ==================== 第 10 课 天气 ====================
    "unit40": [
        {"title": "看天气", "scene": "早上看窗外", "lines": [
            ("Look at the weather.", "看看今天的天气。"),
            ("It is sunny today.", "太阳可好呢。"),
            ("The forecast is good.", "天气预报说今天不错。"),
        ]},
        {"title": "下雨了", "scene": "路上下起雨来", "lines": [
            ("It is rainy now.", "下雨了。"),
            ("I have my raincoat.", "我穿上雨衣。"),
            ("My shoes are wet.", "鞋子湿透了。"),
            ("I hear thunder!", "我还听见打雷！"),
        ]},
        {"title": "又阴又有风", "scene": "雨停了，天还阴着", "lines": [
            ("It is cloudy and windy.", "天阴阴的，风还挺大。"),
            ("It is ten degrees.", "现在十度。"),
            ("My coat is dry.", "我的外套还没湿。"),
        ]},
    ],
    # ==================== 第 11 课 农场 ====================
    "unit41": [
        {"title": "爷爷的农场", "scene": "到农场，看田和栅栏", "lines": [
            ("This is my grandpa's farm.", "这是我爷爷的农场。"),
            ("The field is very big.", "田特别大。"),
            ("A fence is here.", "边上围着一圈栅栏。"),
        ]},
        {"title": "收小麦", "scene": "地里收小麦和棉花", "lines": [
            ("We harvest the wheat.", "我们收小麦。"),
            ("The cotton grows here.", "这儿也种棉花。"),
            ("The wheat is very good.", "小麦长得特别好。"),
        ]},
        {"title": "装车", "scene": "拖拉机把麦子运进谷仓", "lines": [
            ("My grandpa has a tractor.", "爷爷有一台拖拉机。"),
            ("We load the truck.", "我们把东西装上车。"),
            ("I carry it to the barn.", "我再一趟趟搬进谷仓。"),
        ]},
    ],
    # ==================== 第 12 课 衣服与购物 ====================
    "unit42": [
        {"title": "试毛衣", "scene": "商店里挑毛衣", "lines": [
            ("I try a sweater.", "我拿起一件毛衣试穿。"),
            ("My size is small.", "我穿小号。"),
            ("It fits me!", "正好合身！"),
        ]},
        {"title": "看价格", "scene": "看价签、付钱", "lines": [
            ("The price is very good.", "价格挺合适。"),
            ("It is not expensive.", "一点都不贵。"),
            ("It is cheap.", "很便宜。"),
            ("I pay for it.", "我就付钱买下了。"),
        ]},
        {"title": "校服和裤子", "scene": "回家整理衣服", "lines": [
            ("My uniform is new.", "我的校服是新的。"),
            ("My trousers are here.", "裤子也在这儿。"),
            ("This jacket is for my dad.", "这件夹克是爸爸的。"),
            ("My clothes are clean.", "我的衣服都干干净净。"),
        ]},
    ],
    # ==================== 第 13 课 颜色进阶 ====================
    "unit43": [
        {"title": "彩虹", "scene": "雨后天边出现彩虹", "lines": [
            ("Look at the rainbow!", "快看彩虹！"),
            ("I love this colour.", "我最喜欢这个颜色。"),
            ("Purple is very bright.", "紫色亮闪闪的。"),
        ]},
        {"title": "调颜色", "scene": "拿墨水调色", "lines": [
            ("I mix red and blue ink.", "我把红墨水、蓝墨水调在一起。"),
            ("Now it is grey.", "现在变成灰色了。"),
            ("It is very dark.", "灰灰的，暗暗的。"),
        ]},
        {"title": "我的裙子", "scene": "照镜子看裙子花纹", "lines": [
            ("My dress has a nice pattern.", "我的裙子花纹很好看。"),
            ("It has a stripe and a dot.", "上面有道条纹，还有个小圆点。"),
            ("My shoes are silver.", "我的鞋是银色的。"),
        ]},
    ],
    # ==================== 第 14 课 身体进阶 ====================
    "unit44": [
        {"title": "我的身体", "scene": "做早操，伸伸胳膊踢踢腿", "lines": [
            ("This is my body.", "这就是我的身体。"),
            ("My arms are long.", "我的胳膊长长的。"),
            ("My legs are very strong.", "腿特别有劲。"),
        ]},
        {"title": "摸一摸", "scene": "老师带大家做游戏", "lines": [
            ("Touch your knee.", "摸摸膝盖。"),
            ("Touch your shoulder.", "摸摸肩膀。"),
            ("Touch your head!", "再摸摸头！"),
        ]},
        {"title": "手和脚", "scene": "洗手前看自己的手和脚", "lines": [
            ("Look at my hand.", "看看我的手。"),
            ("This is my thumb.", "这是大拇指。"),
            ("This is my finger.", "这是食指。"),
            ("My toes are here.", "我的小脚趾在这儿呢。"),
        ]},
    ],
    # ==================== 第 15 课 动物园 ====================
    "unit45": [
        {"title": "去动物园", "scene": "进园先看大兽", "lines": [
            ("We visit the zoo.", "我们去动物园。"),
            ("I see a big tiger.", "我看见一只大老虎。"),
            ("The lion is very big.", "狮子也特别大。"),
        ]},
        {"title": "高高的动物", "scene": "继续往里走", "lines": [
            ("The giraffe is very tall.", "长颈鹿好高啊。"),
            ("The elephant is big.", "大象好大。"),
            ("The monkey is so funny!", "猴子太好玩了！"),
        ]},
        {"title": "慢慢的动物", "scene": "最后看爬行动物", "lines": [
            ("The snake is very long.", "蛇长长的。"),
            ("The turtle is very slow.", "乌龟慢吞吞的。"),
            ("The koala is in the tree.", "考拉待在树上。"),
        ]},
    ],
    # ==================== 第 16 课 食物进阶 ====================
    "unit46": [
        {"title": "肚子饿了", "scene": "跑进厨房找吃的", "lines": [
            ("I am hungry.", "我肚子饿了。"),
            ("I go to the kitchen.", "跑去厨房。"),
            ("We have bread and jam.", "我们有面包和果酱。"),
            ("I have a sandwich and jam!", "我拿个三明治，抹上果酱。"),
            ("I love jam and bread!", "我最喜欢果酱面包啦！"),
        ]},
        {"title": "烤蛋糕", "scene": "和妈妈一起烤蛋糕", "lines": [
            ("We have flour and sugar.", "我们有面粉和糖。"),
            ("We bake a cake.", "烤了一个蛋糕。"),
            ("The cake is very sweet.", "蛋糕可甜啦。"),
            ("The butter is very yellow.", "黄油黄澄澄的。"),
        ]},
        {"title": "开饭了", "scene": "晚饭上桌", "lines": [
            ("We have dinner now.", "开饭啦。"),
            ("I have a sandwich and salad.", "我吃三明治和沙拉。"),
            ("The salad is very good.", "沙拉特别好吃。"),
            ("Do you love cream or butter?", "你喜欢奶油还是黄油呀？"),
            ("I love cream!", "我最喜欢奶油了！"),
        ]},
    ],
    # ==================== 第 17 课 生日与派对 ====================
    "unit47": [
        {"title": "请朋友来", "scene": "生日前一天发邀请", "lines": [
            ("My birthday is here.", "我生日到啦。"),
            ("I invite my friends.", "我请朋友们来家里。"),
            ("We have a big party.", "我们开个大派对。"),
            ("I have a gift for Tom.", "我给汤姆准备了一份礼物。"),
        ]},
        {"title": "装饰蛋糕", "scene": "插蜡烛、系丝带", "lines": [
            ("We decorate the cake.", "我们一起装饰蛋糕。"),
            ("The candle is on the cake.", "蛋糕上插着蜡烛。"),
            ("A pink ribbon is here.", "还系了条粉色丝带。"),
            ("What a surprise!", "真让人惊喜！"),
        ]},
        {"title": "派对开心", "scene": "小丑变魔术，大家一起庆祝", "lines": [
            ("A clown is here.", "小丑来啦。"),
            ("He can do magic.", "他会变魔术。"),
            ("We celebrate with joy.", "我们一起庆祝，开心得不得了。"),
        ]},
    ],
    # ==================== 第 18 课 水果进阶 ====================
    "unit48": [
        {"title": "水果摊", "scene": "看摊上的水果", "lines": [
            ("I love fruit.", "我最爱吃水果。"),
            ("This fruit is very fresh.", "这些水果特别新鲜。"),
            ("It is ripe now.", "都熟透了。"),
        ]},
        {"title": "切西瓜", "scene": "回家切西瓜", "lines": [
            ("This watermelon is very big.", "这个西瓜好大。"),
            ("I have a slice.", "我切了一片。"),
            ("It is very sweet!", "甜得很！"),
        ]},
        {"title": "一串葡萄", "scene": "桌上摆着水果拼盘", "lines": [
            ("A bunch of grapes is here.", "这儿有一串葡萄。"),
            ("The blueberry is small.", "蓝莓小小的。"),
            ("The pineapple is not sour.", "菠萝一点都不酸。"),
        ]},
    ],
    # ==================== 第 19 课 数字进阶 ====================
    "unit49": [
        {"title": "数星星", "scene": "晚上躺在草地上数星星", "lines": [
            ("I count the stars.", "我数天上的星星。"),
            ("My number is twenty.", "我数到二十。"),
            ("I see twenty stars!", "一共二十颗！"),
        ]},
        {"title": "很多球", "scene": "整理玩具球", "lines": [
            ("I have many balls.", "我有很多球。"),
            ("Eleven are red.", "十一个是红的。"),
            ("Twelve are blue.", "十二个是蓝的。"),
        ]},
        {"title": "一百朵花", "scene": "数花装瓶", "lines": [
            ("We have thirty flowers.", "我们有三十朵花。"),
            ("I have fifteen flowers here.", "我这儿还有十五朵。"),
            ("Now it is a hundred!", "合起来正好一百朵！"),
        ]},
    ],
    # ==================== 第 20 课 玩具与游戏 ====================
    "unit50": [
        {"title": "玩骰子游戏", "scene": "和爸爸玩掷骰子", "lines": [
            ("We have a game.", "我们玩个游戏。"),
            ("I have the dice.", "骰子在我手上。"),
            ("I win the game!", "我赢啦！"),
            ("It is fun.", "太好玩了。"),
        ]},
        {"title": "看动画", "scene": "拿平板看动画片", "lines": [
            ("I look at the screen.", "我盯着屏幕看。"),
            ("A cartoon is on.", "上面在放动画片。"),
            ("My tablet is here.", "平板就在我手里。"),
            ("This video is good.", "这个片子真不错。"),
        ]},
        {"title": "下棋输了", "scene": "和 Tom 下棋，输一局", "lines": [
            ("Chess is my game.", "我最爱下棋。"),
            ("I lose today.", "今天输了一局。"),
            ("I have a big marble.", "我兜里还有颗大弹珠呢。"),
            ("I am happy.", "照样高兴。"),
        ]},
    ],
    # ==================== 第 21 课 方位与位置 ====================
    "unit51": [
        {"title": "猫藏哪儿了", "scene": "屋里找猫", "lines": [
            ("My cat is not here.", "我的猫不见啦。"),
            ("It is behind the door.", "在门后头。"),
            ("It is beside my chair!", "原来在我椅子旁边！"),
        ]},
        {"title": "球在中间", "scene": "球卡在椅子中间", "lines": [
            ("The ball is in the middle.", "球在正中间。"),
            ("It is between two chairs.", "夹在两把椅子中间。"),
            ("It is not on the top.", "不在最上面。"),
            ("It is at the bottom.", "在最底下。"),
        ]},
        {"title": "跑一圈", "scene": "绕操场跑", "lines": [
            ("We run around the field.", "我们绕着操场跑一圈。"),
            ("We run along the path.", "顺着小路跑。"),
            ("We jump over the grass.", "再跳过草地。"),
            ("This is a good place!", "这地方真好玩！"),
        ]},
    ],
    # ==================== 第 22 课 星期与月份 ====================
    "unit52": [
        {"title": "星期一", "scene": "早上看日历", "lines": [
            ("Today is Monday.", "今天是星期一。"),
            ("Tomorrow is Tuesday.", "明天就是星期二。"),
            ("I have English today.", "今天有英语课。"),
        ]},
        {"title": "生日在二月", "scene": "翻到二月那一页", "lines": [
            ("My birthday is in February.", "我的生日在二月。"),
            ("February is a cold month.", "二月是很冷的月份。"),
            ("I love this month!", "我就喜欢这个月！"),
        ]},
        {"title": "夏天游泳", "scene": "暑假天天去游泳", "lines": [
            ("June is hot.", "六月很热。"),
            ("July is very hot.", "七月更热。"),
            ("We swim in summer.", "整个夏天我们都在游泳。"),
        ]},
    ],
    # ==================== 第 23 课 节日 ====================
    "unit53": [
        {"title": "圣诞节", "scene": "过节前几天准备礼物", "lines": [
            ("Christmas is a big holiday.", "圣诞节是个大节日。"),
            ("I love this festival.", "我特别喜欢这一天。"),
            ("I have a gift for my mum.", "我给妈妈准备了礼物。"),
        ]},
        {"title": "万圣节", "scene": "抱着南瓜、戴面具", "lines": [
            ("Halloween is here.", "万圣节到啦。"),
            ("I have a big pumpkin.", "我抱了个大南瓜。"),
            ("My mask is funny.", "我的面具特别搞笑。"),
            ("We have a treat!", "还有甜甜的糖果！"),
        ]},
        {"title": "看游行", "scene": "晚上看龙灯和烟花", "lines": [
            ("We see a parade.", "我们去看游行。"),
            ("A dragon is here.", "龙灯过来了。"),
            ("My lantern is red.", "我的灯笼红红的。"),
            ("The firework is bright!", "烟花一下子亮起来！"),
        ]},
    ],
    # ==================== 第 24 课 自然与世界 ====================
    "unit54": [
        {"title": "我们的世界", "scene": "看地球仪", "lines": [
            ("Look at our world.", "看看我们的世界。"),
            ("The earth is very big.", "地球特别大。"),
            ("I love nature.", "我最喜欢大自然。"),
        ]},
        {"title": "森林和湖", "scene": "走到山脚下", "lines": [
            ("The forest is green.", "森林绿油油的。"),
            ("A lake is near the hill.", "小山旁边有个湖。"),
            ("The valley is very quiet.", "山谷里安安静静。"),
        ]},
        {"title": "海边", "scene": "到沙滩上看海", "lines": [
            ("I sit on the sand.", "我坐在沙滩上。"),
            ("A big wave is here.", "一个大浪打过来。"),
            ("I see a rock and a bridge.", "远处有块大石头，还有一座桥。"),
        ]},
    ],
}
