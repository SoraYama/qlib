import React from 'react'
import { Routes, Route } from 'react-router-dom'
import { Layout } from 'antd'

import AppLayout from './components/Layout/AppLayout'
import Dashboard from './pages/Dashboard'
import DataManager from './pages/DataManager'
import ModelTrainer from './pages/ModelTrainer'
import BacktestPanel from './pages/BacktestPanel'
import TradingPanel from './pages/TradingPanel'

const { Content } = Layout

const App: React.FC = () => {
  return (
    <AppLayout>
      <Content style={{ padding: '24px', minHeight: 'calc(100vh - 64px)' }}>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/data" element={<DataManager />} />
          <Route path="/model" element={<ModelTrainer />} />
          <Route path="/backtest" element={<BacktestPanel />} />
          <Route path="/trading" element={<TradingPanel />} />
        </Routes>
      </Content>
    </AppLayout>
  )
}

export default App
