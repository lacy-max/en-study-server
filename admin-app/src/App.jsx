import React, { useEffect, useState } from 'react'
import { Layout, Menu, Dropdown, Button, Avatar, Typography } from 'antd'
import {
  DashboardOutlined,
  BookOutlined,
  TeamOutlined,
  LogoutOutlined,
  UserOutlined
} from '@ant-design/icons'
import Overview from './pages/Overview'
import Chapters from './pages/Chapters'
import Students from './pages/Students'
import Login from './pages/Login'
import { getToken, setToken } from './api'

const { Sider, Content, Header } = Layout
const { Text } = Typography

const MENU = [
  { key: 'overview', icon: <DashboardOutlined />, label: '数据概览' },
  { key: 'chapters', icon: <BookOutlined />, label: '题库管理' },
  { key: 'students', icon: <TeamOutlined />, label: '学员学习' }
]

export default function App() {
  const [session, setSession] = useState(getToken() ? { token: getToken() } : null)
  const [tab, setTab] = useState('overview')

  useEffect(() => {
    if (!session) setToken('')
  }, [session])

  if (!session) {
    return <Login onSuccess={s => setSession(s)} />
  }

  const logout = () => {
    setToken('')
    setSession(null)
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
        <Header
          style={{
            background: '#fff',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'flex-end',
            gap: 12,
            paddingInline: 24,
            borderBottom: '1px solid #eef0f6',
            height: 56
          }}
        >
          <Dropdown
            menu={{
              items: [{ key: 'logout', icon: <LogoutOutlined />, label: '退出登录', onClick: logout }]
            }}
          >
            <Button type='text'>
              <Avatar size={24} icon={<UserOutlined />} style={{ marginRight: 8 }} />
              <Text>管理员</Text>
            </Button>
          </Dropdown>
        </Header>

        <Content style={{ padding: 24 }}>
          {tab === 'overview' && <Overview goTo={setTab} />}
          {tab === 'chapters' && <Chapters />}
          {tab === 'students' && <Students />}
        </Content>
      </Layout>
    </Layout>
  )
}
