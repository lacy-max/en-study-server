import React, { useEffect, useMemo, useState } from 'react'
import {
  Table,
  Button,
  Space,
  Drawer,
  Form,
  Input,
  message,
  Tag,
  Popconfirm,
  Alert
} from 'antd'
import {
  fetchChapters,
  saveChapter,
  removeChapter,
  reorderChapters
} from '../api'

const { TextArea } = Input

function wordsToText(words) {
  return (words || [])
    .map(w => [w.en, w.cn, w.answer, w.sentence, w.sentenceCn].map(x => x || '').join(' | '))
    .join('\n')
}

function textToWords(text) {
  return String(text || '')
    .split('\n')
    .map(l => l.trim())
    .filter(Boolean)
    .map(line => {
      const parts = line.split(/\s*[|\t]\s*/)
      const en = (parts[0] || '').trim()
      return {
        en,
        cn: (parts[1] || '').trim(),
        answer: (parts[2] || en).trim(),
        sentence: (parts[3] || '').trim(),
        sentenceCn: (parts[4] || '').trim()
      }
    })
    .filter(w => w.en)
}

export default function Chapters() {
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)
  const [editingId, setEditingId] = useState(null)
  const [form] = Form.useForm()

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

  const openEditor = (unit) => {
    setEditingId(unit ? unit.id : null)
    setOpen(true)
    setTimeout(() => {
      form.setFieldsValue({
        id: unit ? unit.id : `unit${String(units.length + 1).padStart(2, '0')}`,
        title: unit ? unit.title : '',
        subtitle: unit ? unit.subtitle : '',
        words: wordsToText(unit ? unit.words : []),
        sentences: (unit ? unit.sentences || [] : []).join('\n')
      })
    }, 0)
  }

  const submit = async () => {
    const v = await form.validateFields()
    const words = textToWords(v.words)
    if (!words.length) {
      message.error('单词表不能为空')
      return
    }
    const noCn = words.filter(w => !w.cn).length
    const unit = {
      id: v.id.trim(),
      title: v.title.trim(),
      subtitle: v.subtitle?.trim() || `生词 ${words.length} 个 · 巩固练习`,
      words,
      sentences: String(v.sentences || '')
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

  const del = async (id) => {
    try {
      await removeChapter(id)
      message.success('已删除')
      await load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = useMemo(
    () => [
      {
        title: '#',
        width: 56,
        render: (_, __, i) => i + 1
      },
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
        title: '单词',
        width: 90,
        render: (_, r) => (r.words || []).length
      },
      {
        title: '例句',
        width: 90,
        render: (_, r) => (r.sentences || []).length
      },
      {
        title: '副标题',
        dataIndex: 'subtitle',
        ellipsis: true
      },
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
      </Space>

      <Table
        rowKey='id'
        dataSource={units}
        scroll={{ x: 860 }}
        columns={columns}
        loading={loading}
        pagination={false}
        size='middle'
        style={{ background: '#fff', borderRadius: 12, padding: 8 }}
      />

      <Drawer
        title={editingId ? `编辑：${editingId}` : '新建单元'}
        width={720}
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
        <Alert
          type='info'
          showIcon
          style={{ marginBottom: 16 }}
          message='单词表每行一个词，用 | 分隔：英文 | 中文 | 挖空答案 | 例句 | 例句中文'
          description='只填「英文 | 中文」也行，会自动把英文当挖空答案；例句留空则该词不进交叉练习。'
        />
        <Form form={form} layout='vertical'>
          <Form.Item name='id' label='单元 id（唯一，不要重复）' rules={[{ required: true, message: '请填 id' }]}>
            <Input placeholder='unit11' />
          </Form.Item>
          <Form.Item name='title' label='标题' rules={[{ required: true, message: '请填标题' }]}>
            <Input placeholder='Unit 11 · 校园生活' />
          </Form.Item>
          <Form.Item name='subtitle' label='副标题（可不填）'>
            <Input placeholder='生词 20 个 · 巩固练习' />
          </Form.Item>
          <Form.Item name='words' label='单词表' rules={[{ required: true, message: '单词表不能为空' }]}>
            <TextArea rows={10} placeholder='hello | 你好 | hello | I said hello to her. | 我跟她打招呼了。' />
          </Form.Item>
          <Form.Item name='sentences' label='句子填空的句子（每行一句，纯英文，不要预先挖空）'>
            <TextArea rows={6} placeholder='I will call you soon.' />
          </Form.Item>
        </Form>
      </Drawer>
    </div>
  )
}
