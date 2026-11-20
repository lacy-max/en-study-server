import React, { useEffect, useState } from 'react'
import { Table, Button, Tag, message, Popconfirm, Space } from 'antd'
import { fetchChapters, fetchStudents, removeStudent } from '../api'

export default function Students() {
  const [rows, setRows] = useState([])
  const [units, setUnits] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const [list, chs] = await Promise.all([fetchStudents(), fetchChapters().catch(() => [])])
      setRows(Array.isArray(list) ? list : [])
      setUnits(Array.isArray(chs) ? chs : [])
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const titleOf = id => {
    const u = units.find(x => x.id === id)
    return u ? u.title.replace(/^Unit\s*\d+\s*·\s*/, '') : id
  }

  const columns = [
    {
      title: '昵称',
      dataIndex: 'name',
      render: v => <b>{v}</b>
    },
    {
      title: '活跃度',
      dataIndex: 'status',
      width: 110,
      render: v =>
        v === 'active' ? (
          <Tag color='green'>活跃</Tag>
        ) : v === 'half' ? (
          <Tag color='orange'>半活跃</Tag>
        ) : (
          <Tag color='default'>不活跃</Tag>
        )
    },
    {
      title: '手机号',
      dataIndex: 'phone',
      width: 150,
      render: v => v || <span style={{ color: '#b0b6cc' }}>未填</span>
    },
    {
      title: '性别',
      dataIndex: 'gender',
      width: 90,
      render: v =>
        v === 'girl' ? (
          <Tag color='magenta'>👧 女孩</Tag>
        ) : v === 'boy' ? (
          <Tag color='blue'>👦 男孩</Tag>
        ) : (
          <span style={{ color: '#b0b6cc' }}>未选</span>
        )
    },
    {
      title: '已学单元',
      dataIndex: 'chapterCount',
      width: 120,
      render: v => <Tag color={v ? 'green' : 'default'}>{v} 个</Tag>
    },
    {
      title: '学习进度明细',
      render: (_, r) => {
        const entries = Object.entries(r.chapters || {})
        if (!entries.length) return <span style={{ color: '#b0b6cc' }}>还没开始</span>
        return (
          <Space size={4} wrap>
            {entries.map(([id, score]) => (
              <Tag key={id} color='geekblue'>
                {titleOf(id)} · {Math.round(score)}分
              </Tag>
            ))}
          </Space>
        )
      }
    },
    {
      title: '最近学习',
      dataIndex: 'lastStudyAt',
      width: 180,
      render: v => (v ? new Date(v).toLocaleString() : '—')
    },
    {
      title: '操作',
      width: 100,
      render: (_, r) => (
        <Popconfirm
          title={`删除学员「${r.name}」？进度会一起删除`}
          onConfirm={async () => {
            try {
              await removeStudent(r.uid)
              message.success('已删除')
              load()
            } catch (e) {
              message.error(e.message)
            }
          }}
        >
          <Button size='small' danger>
            删除
          </Button>
        </Popconfirm>
      )
    }
  ]

  return (
    <div>
      <h3 className='page-title'>学员列表</h3>
      <p className='page-sub'>学员在手机端登录后，资料与进度自动同步到这里</p>
      <Button onClick={load} loading={loading} style={{ marginBottom: 16 }}>
        刷新
      </Button>
      <Table
        rowKey='uid'
        dataSource={rows}
        scroll={{ x: 1140 }}
        columns={columns}
        loading={loading}
        pagination={false}
        size='middle'
        locale={{ emptyText: '还没有学员注册，让学员在手机端先登录一次' }}
        style={{ background: '#fff', borderRadius: 12, padding: 8 }}
      />
    </div>
  )
}
