import React, { useEffect, useState } from 'react'
import { Table, Button, Tag, message, Popconfirm, Space } from 'antd'
import { fetchFeedback, removeFeedback } from '../api'


function fmt(v) {
  if (!v) return '—'
  return new Date(v).toLocaleString('zh-CN', { hour12: false })
}

export default function Feedback() {
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)

  const load = async () => {
    setLoading(true)
    try {
      const list = await fetchFeedback()
      setRows(Array.isArray(list) ? list : [])
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    load()
  }, [])

  const del = async fid => {
    try {
      await removeFeedback(fid)
      message.success('已删除')
      load()
    } catch (e) {
      message.error(e.message)
    }
  }

  const columns = [
    {
      title: '时间',
      dataIndex: 'created_at',
      width: 190,
      render: v => fmt(v || 0)
    },
    {
      title: '昵称',
      dataIndex: 'name',
      width: 140,
      render: v => (v ? <Tag color='blue'>{v}</Tag> : <span style={{ color: '#b0b6cc' }}>未登录</span>)
    },
    {
      title: '账号 ID',
      dataIndex: 'uid',
      width: 200,
      render: v => (
        <span style={{ fontFamily: 'monospace', fontSize: 12, color: '#6b7280' }}>
          {v || '—'}
        </span>
      )
    },
    {
      title: '反馈内容',
      dataIndex: 'text',
      render: v => <span style={{ display: 'block', whiteSpace: 'pre-wrap', lineHeight: 1.6 }}>{v}</span>
    },
    {
      title: '操作',
      width: 100,
      render: (_, r) => (
        <Popconfirm title='确定删除这条反馈？' onConfirm={() => del(r.id)}>
          <Button danger type='link' size='small'>删除</Button>
        </Popconfirm>
      )
    }
  ]

  return (
    <div>
      <Space style={{ marginBottom: 16 }}>
        <Button onClick={load} loading={loading}>刷新</Button>
        <span style={{ color: '#8a90a5' }}>共 {rows.length} 条反馈</span>
      </Space>
      <Table
        rowKey='id'
        loading={loading}
        columns={columns}
        dataSource={rows}
        scroll={{ x: 860 }}
        pagination={{ pageSize: 10, showSizeChanger: false }}
        locale={{ emptyText: '还没有用户反馈' }}
      />
    </div>
  )
}
