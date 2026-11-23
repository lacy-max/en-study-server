import React, { useEffect, useMemo, useState } from 'react'
import {
  Table,
  Button,
  Space,
  Drawer,
  Input,
  message,
  Tag,
  Popconfirm,
  Select,
  Empty
} from 'antd'
import {
  fetchChapters,
  saveChapter,
  removeChapter,
  reorderChapters
} from '../api'

const { TextArea } = Input

// 课程难度阶梯（与学员端 src/data/levels.js 保持一致）
const LEVELS = [
  { key: 'L0', name: 'L0 启蒙', age: '3–6 岁', desc: '字母、问候、颜色、数字、动物、家人' },
  { key: 'L1', name: 'L1 小学低段', age: '小学 1–3 年级', desc: '日常生活名词与最常用动词' },
  { key: 'L2', name: 'L2 小学高段', age: '小学 3–6 年级', desc: '话题扩展、形容词、简单短语' },
  { key: 'L3', name: 'L3 初中', age: '初中 7–9 年级', desc: '课标核心词与常见搭配' },
  { key: 'L4', name: 'L4 高中', age: '高中', desc: '3500 词表、抽象名词与从句' },
  { key: 'L5', name: 'L5 四级', age: '大学 · CET-4', desc: '4500 词、学术与社会话题' },
  { key: 'L6', name: 'L6 六级', age: '大学 · CET-6', desc: '5500–6000 词、进阶抽象词' }
]

const LEVEL_TAG = { L0: 'purple', L1: 'geekblue', L2: 'blue', L3: 'green', L4: 'orange', L5: 'red', L6: 'magenta' }

function levelOf(unit) {
  const k = String((unit && unit.level) || 'L0').toUpperCase()
  return LEVELS.some(l => l.key === k) ? k : 'L0'
}

function levelName(key) {
  const hit = LEVELS.filter(l => l.key === key)[0]
  return hit ? `${hit.name} · ${hit.age}` : key
}

/* ---------- 数据结构：单词 → 例句 → 词块 ---------- */

function normalizeChunks(s) {
  if (Array.isArray(s.chunks) && s.chunks.length) {
    return s.chunks.map(c => ({ en: c.en || '', cn: c.cn || '' }))
  }
  if (s.en) return [{ en: s.en, cn: s.cn || '' }]
  return [{ en: '', cn: '' }]
}

function normalizeSentences(w) {
  if (Array.isArray(w.sentences) && w.sentences.length) {
    return w.sentences.map(s => ({ chunks: normalizeChunks(s) }))
  }
  if (w.sentence) return [{ chunks: normalizeChunks({ en: w.sentence, cn: w.sentenceCn, chunks: w.chunks }) }]
  return []
}

function normalizeWord(w) {
  return {
    en: w.en || '',
    cn: w.cn || '',
    ipa: w.ipa || '',
    ipaUs: w.ipaUs || '',
    answer: w.answer || '',
    emoji: w.emoji || '',
    sentences: normalizeSentences(w)
  }
}

function sentenceEn(s) {
  return (s.chunks || [])
    .map(c => (c.en || '').trim())
    .filter(Boolean)
    .join(' ')
}

function sentenceCn(s) {
  return (s.chunks || [])
    .map(c => (c.cn || '').trim())
    .filter(Boolean)
    .join('')
}

/* ---------- 页面 ---------- */

export default function Chapters() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [draft, setDraft] = useState(null)
  const [active, setActive] = useState(0)
  const [q, setQ] = useState('')

  const load = async () => {
    setLoading(true)
    try {
      const list = await fetchChapters()
      setUnits(Array.isArray(list) ? list : [])
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const openEditor = unit => {
    const words = ((unit && unit.words) || []).map(normalizeWord)
    setDraft({
      base: unit || null,
      id: unit ? unit.id : `unit${String(units.length + 1).padStart(2, '0')}`,
      level: levelOf(unit),
      title: unit ? unit.title || '' : '',
      subtitle: unit ? unit.subtitle || '' : '',
      fill: ((unit && unit.sentences) || []).join('\n'),
      words: words.length ? words : []
    })
    setActive(0)
    setOpen(true)
  }

  const patchDraft = patch => setDraft(d => ({ ...d, ...patch }))

  const patchWord = (i, patch) =>
    setDraft(d => {
      const words = d.words.slice()
      words[i] = { ...words[i], ...patch }
      return { ...d, words }
    })

  const addWord = () =>
    setDraft(d => {
      const words = d.words.concat([
        { en: '', cn: '', ipa: '', ipaUs: '', answer: '', emoji: '', sentences: [{ chunks: [{ en: '', cn: '' }] }] }
      ])
      setActive(words.length - 1)
      return { ...d, words }
    })

  const removeWord = i =>
    setDraft(d => {
      const words = d.words.filter((_, j) => j !== i)
      return { ...d, words }
    })

  const moveWord = (i, dir) =>
    setDraft(d => {
      const j = i + dir
      if (j < 0 || j >= d.words.length) return d
      const words = d.words.slice()
      const t = words[i]
      words[i] = words[j]
      words[j] = t
      setActive(j)
      return { ...d, words }
    })

  const patchSentence = (wi, si, patch) =>
    setDraft(d => {
      const words = d.words.slice()
      const sentences = words[wi].sentences.slice()
      sentences[si] = { ...sentences[si], ...patch }
      words[wi] = { ...words[wi], sentences }
      return { ...d, words }
    })

  const patchChunk = (wi, si, ci, patch) =>
    setDraft(d => {
      const words = d.words.slice()
      const sentences = words[wi].sentences.slice()
      const chunks = sentences[si].chunks.slice()
      chunks[ci] = { ...chunks[ci], ...patch }
      sentences[si] = { ...sentences[si], chunks }
      words[wi] = { ...words[wi], sentences }
      return { ...d, words }
    })

  const addChunk = (wi, si) =>
    setDraft(d => {
      const words = d.words.slice()
      const sentences = words[wi].sentences.slice()
      sentences[si] = { ...sentences[si], chunks: sentences[si].chunks.concat([{ en: '', cn: '' }]) }
      words[wi] = { ...words[wi], sentences }
      return { ...d, words }
    })

  const removeChunk = (wi, si, ci) =>
    setDraft(d => {
      const words = d.words.slice()
      const sentences = words[wi].sentences.slice()
      sentences[si] = { ...sentences[si], chunks: sentences[si].chunks.filter((_, j) => j !== ci) }
      words[wi] = { ...words[wi], sentences }
      return { ...d, words }
    })

  const moveChunk = (wi, si, ci, dir) =>
    setDraft(d => {
      const words = d.words.slice()
      const sentences = words[wi].sentences.slice()
      const chunks = sentences[si].chunks.slice()
      const j = ci + dir
      if (j < 0 || j >= chunks.length) return d
      const t = chunks[ci]
      chunks[ci] = chunks[j]
      chunks[j] = t
      sentences[si] = { ...sentences[si], chunks }
      words[wi] = { ...words[wi], sentences }
      return { ...d, words }
    })

  const addSentence = wi =>
    setDraft(d => {
      const words = d.words.slice()
      words[wi] = { ...words[wi], sentences: words[wi].sentences.concat([{ chunks: [{ en: '', cn: '' }] }]) }
      return { ...d, words }
    })

  const removeSentence = (wi, si) =>
    setDraft(d => {
      const words = d.words.slice()
      words[wi] = { ...words[wi], sentences: words[wi].sentences.filter((_, j) => j !== si) }
      return { ...d, words }
    })

  const submit = async () => {
    if (!draft) return
    if (!draft.id.trim()) {
      message.error('请填单元 id')
      return
    }
    const words = draft.words.filter(w => w.en.trim())
    if (!words.length) {
      message.error('至少加一个单词')
      return
    }
    const badSentence = words.filter(w => w.sentences.some(s => !sentenceEn(s)))
    if (badSentence.length) {
      message.error(`有 ${badSentence.length} 个单词的例句还没填词块，先补上或删掉`)
      return
    }
    const noCn = words.filter(w => !w.cn.trim()).length
    const outWords = words.map(w => {
      const sentences = w.sentences
        .map(s => ({
          en: sentenceEn(s),
          cn: sentenceCn(s),
          chunks: s.chunks.filter(c => (c.en || '').trim()).map(c => ({ en: c.en.trim(), cn: (c.cn || '').trim() }))
        }))
        .filter(s => s.en)
      const first = sentences[0] || { en: '', cn: '', chunks: [] }
      return {
        en: w.en.trim(),
        cn: w.cn.trim(),
        ipa: w.ipa.trim(),
        ipaUs: w.ipaUs.trim(),
        answer: (w.answer || w.en).trim(),
        emoji: w.emoji || '',
        sentence: first.en,
        sentenceCn: first.cn,
        chunks: first.chunks,
        sentences
      }
    })
    const base = draft.base || {}
    const unit = {
      ...base,
      id: draft.id.trim(),
      level: draft.level,
      title: draft.title.trim(),
      subtitle: draft.subtitle.trim() || `生词 ${outWords.length} 个 · 巩固练习`,
      words: outWords,
      sentences: draft.fill
        .split('\n')
        .map(s => s.trim())
        .filter(Boolean)
    }
    try {
      await saveChapter(unit)
      message.success(noCn ? `已保存，其中 ${noCn} 个单词没有中文释义` : '已保存')
      setOpen(false)
      await load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const move = async (index, dir) => {
    const j = index + dir
    if (j < 0 || j >= units.length) return
    const ids = units.map(u => u.id)
    ;[ids[index], ids[j]] = [ids[j], ids[index]]
    try {
      await reorderChapters(ids)
      await load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const del = async id => {
    try {
      await removeChapter(id)
      message.success('已删除')
      await load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const shownUnits = useMemo(() => {
    const k = q.trim().toLowerCase()
    if (!k) return units
    return units.filter(u => [u.title, u.id, u.subtitle, (u.words || []).map(w => `${w.en} ${w.cn}`).join(' ')]
      .filter(Boolean)
      .some(x => String(x).toLowerCase().indexOf(k) >= 0))
  }, [units, q])

  const columns = useMemo(
    () => [
      { title: '#', width: 56, render: (_, __, i) => i + 1 },
      {
        title: '单元',
        dataIndex: 'title',
        render: (t, r) => (
          <span>
            <b>{t}</b>
            <Tag color='geekblue' style={{ marginLeft: 8 }}>
              {r.id}
            </Tag>
          </span>
        )
      },
      {
        title: '阶梯',
        width: 190,
        filters: LEVELS.map(l => ({ text: `${l.key} · ${l.age}`, value: l.key })),
        onFilter: (val, r) => levelOf(r) === val,
        render: (_, r) => {
          const k = levelOf(r)
          return <Tag color={LEVEL_TAG[k]}>{levelName(k)}</Tag>
        }
      },
      { title: '单词', width: 90, render: (_, r) => (r.words || []).length },
      {
        title: '例句',
        width: 110,
        render: (_, r) => (r.words || []).reduce((n, w) => n + ((w.sentences || []).length || 1), 0)
      },
      { title: '副标题', dataIndex: 'subtitle', ellipsis: true },
      {
        title: '操作',
        width: 240,
        render: (_, r, i) => (
          <Space size={4}>
            <Button size='small' onClick={() => move(i, -1)} disabled={i === 0}>
              上移
            </Button>
            <Button size='small' onClick={() => move(i, 1)} disabled={i === units.length - 1}>
              下移
            </Button>
            <Button size='small' type='primary' ghost onClick={() => openEditor(r)}>
              编辑
            </Button>
            <Popconfirm title={`确定删除「${r.title}」？`} onConfirm={() => del(r.id)}>
              <Button size='small' danger>
                删除
              </Button>
            </Popconfirm>
          </Space>
        )
      }
    ],
    [units]
  )

  const cur = draft && draft.words[active]

  return (
    <div>
      <h3 className='page-title'>题库管理</h3>
      <p className='page-sub'>
        一个单元 = 一个关卡 = 一次任务。保存后学员端下次打开就能看到，无需重新发布
      </p>

      <Space style={{ marginBottom: 16 }}>
        <Button type='primary' onClick={() => openEditor(null)}>
          ＋ 新建单元
        </Button>
        <Button onClick={load} loading={loading}>
          刷新
        </Button>
        <Input.Search
          allowClear
          placeholder='搜单元 id / 标题 / 单词'
          value={q}
          onChange={e => setQ(e.target.value)}
          style={{ width: 300 }}
        />
        <span style={{ color: '#8a90a5' }}>共 {shownUnits.length} 个单元</span>
      </Space>

      <Table
        rowKey='id'
        dataSource={shownUnits}
        scroll={{ x: 860 }}
        columns={columns}
        loading={loading}
        pagination={{
          pageSize: 10,
          showSizeChanger: true,
          pageSizeOptions: ['10', '20', '50'],
          showTotal: t => `共 ${t} 个单元`
        }}
        size='middle'
        style={{ background: '#fff', borderRadius: 12, padding: 8 }}
      />

      <Drawer
        title={draft && draft.id ? `编辑：${draft.id}` : '新建单元'}
        width={1040}
        open={open}
        onClose={() => setOpen(false)}
        destroyOnClose
        extra={
          <Space>
            <Button onClick={() => setOpen(false)}>取消</Button>
            <Button type='primary' onClick={submit}>
              保存
            </Button>
          </Space>
        }
      >
        {draft ? (
          <div style={{ display: 'flex', gap: 20, alignItems: 'flex-start' }}>
            {/* 左栏：单元信息 + 单词列表 */}
            <div style={{ width: 320, flex: '0 0 320px' }}>
              <div style={{ background: '#fff', border: '1px solid #eef0f6', borderRadius: 12, padding: 12 }}>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>单元 id</div>
                  <Input value={draft.id} onChange={e => patchDraft({ id: e.target.value })} />
                </div>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>难度阶梯</div>
                  <Select
                    style={{ width: '100%' }}
                    value={draft.level}
                    onChange={v => patchDraft({ level: v })}
                    options={LEVELS.map(l => ({ value: l.key, label: `${l.name} · ${l.age}` }))}
                  />
                </div>
                <div style={{ marginBottom: 8 }}>
                  <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>标题</div>
                  <Input value={draft.title} onChange={e => patchDraft({ title: e.target.value })} />
                </div>
                <div>
                  <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>副标题（可不填）</div>
                  <Input value={draft.subtitle} onChange={e => patchDraft({ subtitle: e.target.value })} />
                </div>
              </div>

              <div style={{ margin: '16px 0 8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <b>单词（{draft.words.length}）</b>
                <Button size='small' type='primary' ghost onClick={addWord}>
                  ＋ 新增单词
                </Button>
              </div>

              <div style={{ display: 'flex', flexDirection: 'column', gap: 8, maxHeight: 520, overflowY: 'auto' }}>
                {draft.words.length === 0 ? <Empty description='还没有单词' /> : null}
                {draft.words.map((w, i) => (
                  <div
                    key={i}
                    onClick={() => setActive(i)}
                    style={{
                      cursor: 'pointer',
                      background: i === active ? '#eef0ff' : '#fff',
                      border: i === active ? '1px solid #b6b9f5' : '1px solid #eef0f6',
                      borderRadius: 10,
                      padding: '10px 12px'
                    }}
                  >
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <div>
                        <b style={{ color: '#4b56d2' }}>{w.en || '（未填英文）'}</b>
                        <span style={{ color: '#98a0bd', fontSize: 12, marginLeft: 8 }}>{w.ipa}</span>
                      </div>
                      <Space size={2} onClick={e => e.stopPropagation()}>
                        <Button size='small' type='text' onClick={() => moveWord(i, -1)} disabled={i === 0}>
                          ↑
                        </Button>
                        <Button
                          size='small'
                          type='text'
                          onClick={() => moveWord(i, 1)}
                          disabled={i === draft.words.length - 1}
                        >
                          ↓
                        </Button>
                        <Popconfirm title='删掉这个单词？' onConfirm={() => removeWord(i)}>
                          <Button size='small' type='text' danger>
                            ✕
                          </Button>
                        </Popconfirm>
                      </Space>
                    </div>
                    <div style={{ fontSize: 12, color: '#666f8c', marginTop: 2 }}>
                      {w.cn || '（未填中文）'} · 例句 {w.sentences.length}
                    </div>
                  </div>
                ))}
              </div>

              <div style={{ marginTop: 16 }}>
                <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>句子填空用句（每行一句）</div>
                <TextArea rows={3} value={draft.fill} onChange={e => patchDraft({ fill: e.target.value })} />
              </div>
            </div>

            {/* 右栏：当前单词的字段 + 例句块编辑 */}
            <div style={{ flex: 1, minWidth: 0 }}>
              {cur ? (
                <div>
                  <div style={{ background: '#fff', border: '1px solid #eef0f6', borderRadius: 12, padding: 16 }}>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>单词</div>
                        <Input
                          value={cur.en}
                          placeholder='school'
                          onChange={e => patchWord(active, { en: e.target.value })}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>中文意思</div>
                        <Input
                          value={cur.cn}
                          placeholder='学校'
                          onChange={e => patchWord(active, { cn: e.target.value })}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>音标（英）</div>
                        <Input
                          value={cur.ipa}
                          placeholder='/skuːl/'
                          onChange={e => patchWord(active, { ipa: e.target.value })}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>音标（美）</div>
                        <Input
                          value={cur.ipaUs}
                          placeholder='/skuːl/'
                          onChange={e => patchWord(active, { ipaUs: e.target.value })}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>挖空答案（默认同单词）</div>
                        <Input
                          value={cur.answer}
                          placeholder='school'
                          onChange={e => patchWord(active, { answer: e.target.value })}
                        />
                      </div>
                      <div>
                        <div style={{ fontSize: 12, color: '#8b90ab', marginBottom: 4 }}>图标 emoji</div>
                        <Input
                          value={cur.emoji}
                          placeholder='🏫'
                          onChange={e => patchWord(active, { emoji: e.target.value })}
                        />
                      </div>
                    </div>
                  </div>

                  <div style={{ margin: '16px 0 8px', display: 'flex', justifyContent: 'space-between' }}>
                    <b>例句（{cur.sentences.length}）</b>
                    <Button size='small' type='primary' ghost onClick={() => addSentence(active)}>
                      ＋ 新增例句
                    </Button>
                  </div>

                  {cur.sentences.map((s, si) => (
                    <div
                      key={si}
                      style={{
                        background: '#fff',
                        border: '1px solid #eef0f6',
                        borderRadius: 12,
                        padding: 14,
                        marginBottom: 12
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <span style={{ fontSize: 12, color: '#8b90ab' }}>例句 {si + 1}</span>
                        <Popconfirm title='删掉这条例句？' onConfirm={() => removeSentence(active, si)}>
                          <Button size='small' type='text' danger disabled={cur.sentences.length <= 1}>
                            删除例句
                          </Button>
                        </Popconfirm>
                      </div>

                      {s.chunks.map((c, ci) => (
                        <div key={ci} style={{ display: 'flex', gap: 8, alignItems: 'center', marginTop: 8 }}>
                          <Input
                            value={c.en}
                            placeholder='I / am / Tom.'
                            style={{ flex: 1 }}
                            onChange={e => patchChunk(active, si, ci, { en: e.target.value })}
                          />
                          <Input
                            value={c.cn}
                            placeholder='我 / 是 / 汤姆'
                            style={{ flex: 1 }}
                            onChange={e => patchChunk(active, si, ci, { cn: e.target.value })}
                          />
                          <Button size='small' type='text' onClick={() => moveChunk(active, si, ci, -1)} disabled={ci === 0}>
                            ↑
                          </Button>
                          <Button
                            size='small'
                            type='text'
                            onClick={() => moveChunk(active, si, ci, 1)}
                            disabled={ci === s.chunks.length - 1}
                          >
                            ↓
                          </Button>
                          <Button
                            size='small'
                            type='text'
                            danger
                            onClick={() => removeChunk(active, si, ci)}
                            disabled={s.chunks.length <= 1}
                          >
                            ✕
                          </Button>
                        </div>
                      ))}

                      <div style={{ marginTop: 10, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <Button size='small' onClick={() => addChunk(active, si)}>
                          ＋ 添加词块
                        </Button>
                      </div>

                      <div style={{ marginTop: 10, background: '#f7f8fd', borderRadius: 10, padding: '10px 12px' }}>
                        <div style={{ fontSize: 22, color: '#333c5c' }}>{sentenceEn(s) || '（整句会由词块自动拼成）'}</div>
                        <div style={{ fontSize: 13, color: '#8b90ab', marginTop: 4 }}>{sentenceCn(s)}</div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <Empty description='左边先加一个单词' />
              )}
            </div>
          </div>
        ) : null}
      </Drawer>
    </div>
  )
}
