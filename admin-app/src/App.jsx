import React, { useEffect, useState } from 'react'
import { Layout, Menu, Input, Button, message } from 'antd'
import {
  DashboardOutlined,
  BookOutlined,
  TeamOutlined,
  SettingOutlined
} from '@ant-design/icons'
import Overview from './pages/Overview'
import Chapters from './pages/Chapters'
import Students from './pages/Students'
import { getToken, setToken } from './api'

const { Sider, Content } = Layout

const MENU = [
  { key: 'overview', icon: <DashboardOutlined />, label: '数据概览' },
  { key: 'chapters', icon: <BookOutlined />, label: '题库管理' },
  { key: 'students', icon: <TeamOutlined />, label: '学员学习' },
  { key: 'settings', icon: <SettingOutlined />, label: '后台设置' }
]

export default function App() {
  const [tab, setTab] = useState('overview')
  const [token, setTokenState] = useState(getToken())

  useEffect(() => {
    if (token) setToken(token)
  }, [])

  const saveToken = () => {
    setToken(token)
    message.success('管理口令已保存到本机')
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider width={220} theme='dark' style={{ background: '#1f2340' }}>
        <div className='logo-row'>
          <span className='emoji'>📚</span>
          <span>英语闯关后台</span>
        </div>
        <Menu
          theme='dark'
          mode='inline'
          selectedKeys={[tab]}
          onClick={e => setTab(e.key)}
          style={{ background: 'transparent', borderInlineEnd: 'none' }}
          items={MENU.map(m => ({ key: m.key, icon: m.icon, label: m.label }))}
        />
      </Sider>

      <Layout>
        <Content style={{ padding: 24 }}>
          {tab === 'overview' && <Overview goTo={setTab} />}
          {tab === 'chapters' && <Chapters />}
          {tab === 'students' && <Students />}
          {tab === 'settings' && (
            <div style={{ background: '#fff', padding: 24, borderRadius: 14, maxWidth: 560 }}>
              <h3 className='page-title'>后台设置</h3>
              <p className='page-sub'>管理口令用于新增/修改/删除题库，保存在本机浏览器</p>
              <Input
                placeholder='管理口令，例如 xiaoyu'
                value={token}
                onChange={e => setTokenState(e.target.value)}
                style={{ marginBottom: 12 }}
              />
              <Button type='primary' onClick={saveToken}>
                保存口令
              </Button>
            </div>
          )}
        </Content>
      </Layout>
    </Layout>
  )
}
