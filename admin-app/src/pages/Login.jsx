import React, { useState } from 'react'
import { Card, Form, Input, Button, message, Typography } from 'antd'
import { LockOutlined, UserOutlined } from '@ant-design/icons'
import { adminLogin, setToken } from '../api'

const { Title, Text } = Typography

export default function Login({ onSuccess }) {
  const [loading, setLoading] = useState(false)

  const submit = async (values) => {
    setLoading(true)
    try {
      const res = await adminLogin(values.username, values.password)
      setToken(res.token)
      message.success('登录成功')
      onSuccess({ token: res.token, username: res.username })
    } catch (e) {
      message.error(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        background: 'linear-gradient(150deg, #f2f4ff 0%, #eef1ff 45%, #fbf3f8 100%)',
        padding: 24
      }}
    >
      <Card style={{ width: 380, borderRadius: 18, boxShadow: '0 18px 46px rgba(99,102,241,.16)' }}>
        <div style={{ textAlign: 'center', marginBottom: 22 }}>
          <div style={{ fontSize: 34 }}>📚</div>
          <Title level={4} style={{ margin: '8px 0 2px' }}>
            英语闯关 · 管理后台
          </Title>
          <Text type='secondary' style={{ fontSize: 12 }}>
            仅管理员可进入
          </Text>
        </div>

        <Form layout='vertical' onFinish={submit} requiredMark={false}>
          <Form.Item
            name='username'
            label='账号'
            rules={[{ required: true, message: '请输入账号' }]}
          >
            <Input
              size='large'
              prefix={<UserOutlined />}
              placeholder='admin'
              autoComplete='username'
            />
          </Form.Item>
          <Form.Item
            name='password'
            label='口令'
            rules={[{ required: true, message: '请输入口令' }]}
          >
            <Input.Password
              size='large'
              prefix={<LockOutlined />}
              placeholder='管理员口令'
              autoComplete='current-password'
            />
          </Form.Item>
          <Button type='primary' size='large' htmlType='submit' block loading={loading}>
            登录
          </Button>
        </Form>
      </Card>
    </div>
  )
}
