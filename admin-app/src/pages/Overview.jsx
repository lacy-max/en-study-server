import React, { useEffect, useState } from 'react'
import { Row, Col, Card, Statistic, Button, List, Tag, Spin } from 'antd'
import { fetchChapters, fetchStudents } from '../api'

export default function Overview({ goTo }) {
  const [loading, setLoading] = useState(true)
  const [units, setUnits] = useState([])
  const [students, setStudents] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    ;(async () => {
      try {
        const [chs, stu] = await Promise.all([fetchChapters(), fetchStudents().catch(() => [])])
        setUnits(Array.isArray(chs) ? chs : [])
        setStudents(Array.isArray(stu) ? stu : [])
      } catch (e) {
        setError(e.message)
      } finally {
        setLoading(false)
      }
    })()
  }, [])

  if (loading) {
    return (
      <div style={{ padding: 60, textAlign: 'center' }}>
        <Spin />
      </div>
    )
  }

  const wordCount = units.reduce((s, u) => s + (u.words || []).length, 0)
  const sentenceCount = units.reduce((s, u) => s + (u.sentences || []).length, 0)
  const learned = students.reduce((s, u) => s + (u.chapterCount || 0), 0)

  return (
    <div>
      <h3 className='page-title'>数据概览</h3>
      <p className='page-sub'>题库在服务端，学员进度也在服务端；前端只负责展示</p>

      {error ? (
        <Card style={{ marginBottom: 16 }} bodyStyle={{ color: '#cf1322' }}>
          读取失败：{error}（请到「后台设置」检查管理口令）
        </Card>
      ) : null}

      <Row gutter={16}>
        <Col xs={12} sm={12} md={6} lg={6}>
          <Card className='stat-card'>
            <Statistic title='单元' value={units.length} suffix='个' />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6} lg={6}>
          <Card className='stat-card'>
            <Statistic title='单词' value={wordCount} suffix='个' />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6} lg={6}>
          <Card className='stat-card'>
            <Statistic title='例句' value={sentenceCount} suffix='句' />
          </Card>
        </Col>
        <Col xs={12} sm={12} md={6} lg={6}>
          <Card className='stat-card'>
            <Statistic title='学员' value={students.length} suffix='人' />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginTop: 16 }}>
        <Col xs={24} lg={14}>
          <Card
            title='最近单元'
            extra={
              <Button type='link' onClick={() => goTo('chapters')}>
                去题库管理
              </Button>
            }
          >
            <List
              size='small'
              dataSource={units.slice(0, 6)}
              renderItem={(u, i) => (
                <List.Item>
                  <span>
                    <b>{i + 1}.</b> {u.title}
                    <Tag color='geekblue' style={{ marginLeft: 8 }}>
                      {u.id}
                    </Tag>
                  </span>
                  <span style={{ color: '#8d93ad' }}>
                    单词 {(u.words || []).length} · 例句 {(u.sentences || []).length}
                  </span>
                </List.Item>
              )}
            />
          </Card>
        </Col>
        <Col xs={24} lg={10}>
          <Card
            title='学习动态'
            extra={
              <Button type='link' onClick={() => goTo('students')}>
                全部学员
              </Button>
            }
          >
            <div style={{ color: '#8d93ad', marginBottom: 10 }}>已学单元合计：{learned} 次</div>
            <List
              size='small'
              dataSource={students.slice(0, 5)}
              locale={{ emptyText: '还没有学员注册' }}
              renderItem={u => (
                <List.Item>
                  <b>{u.name}</b>
                  <span style={{ color: '#8d93ad' }}>已学 {u.chapterCount} 个单元</span>
                </List.Item>
              )}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
