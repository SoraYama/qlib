import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'

import AppLayout from './components/Layout/AppLayout'
import Dashboard from './pages/Dashboard'

const { Content } = Layout

const App: React.FC = () => {
  return (
    <AppLayout>
      <Content style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/data" element={<div>数据管理页面开发中...</div>} />
          <Route path="/model" element={<div>模型训练页面开发中...</div>} />
          <Route path="/backtest" element={<div>回测分析页面开发中...</div>} />
          <Route path="/trading" element={<div>实盘交易页面开发中...</div>} />
        </Routes>
      </Content>
    </AppLayout>
  )
}

export default App
