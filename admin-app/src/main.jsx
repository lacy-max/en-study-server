import React from 'react'
import ReactDOM from 'react-dom/client'
import { ConfigProvider } from 'antd'
import zhCN from 'antd/locale/zh_CN'
import App from './App'
import './index.css'

const theme = {
  token: {
    colorPrimary: '#6d7bf7',
    borderRadius: 10,
    fontFamily:
      '-apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", Arial, sans-serif'
  }
}

ReactDOM.createRoot(document.getElementById('root')).render(
  <ConfigProvider locale={zhCN} theme={theme}>
    <App />
  </ConfigProvider>
)
