import React, { useEffect } from 'react'
import { Row, Col, Card, Statistic, Typography, Alert, Spin } from 'antd'
import {
  ArrowUpOutlined,
  DollarOutlined,
  TrophyOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined,
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import { fetchDashboardSummary } from '../store/slices/dashboardSlice'

const { Title } = Typography

const Dashboard: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { summary, loading, error } = useSelector((state: RootState) => state.dashboard)

  useEffect(() => {
    dispatch(fetchDashboardSummary())
  }, [dispatch])
  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px 0' }}>
        <Spin size="large" />
        <div style={{ marginTop: 16 }}>加载仪表盘数据中...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div>
        <Title level={2}>交易仪表盘</Title>
        <Alert
          message="加载失败"
          description={error}
          type="error"
          showIcon
          closable
        />
      </div>
    )
  }

  return (
    <div>
      <Title level={2}>交易仪表盘</Title>

      {error && (
        <Alert
          message="数据加载失败"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 关键指标卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总资产"
              value={summary?.account?.total_balance || 0}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="总盈亏"
              value={summary?.account?.total_pnl || 0}
              precision={2}
              prefix={<ArrowUpOutlined />}
              valueStyle={{
                color: (summary?.account?.total_pnl || 0) >= 0 ? '#3f8600' : '#cf1322'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={summary?.account?.daily_pnl || 0}
              precision={2}
              prefix={<ArrowUpOutlined />}
              valueStyle={{
                color: (summary?.account?.daily_pnl || 0) >= 0 ? '#3f8600' : '#cf1322'
              }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={12} lg={6}>
          <Card>
            <Statistic
              title="活跃持仓"
              value={summary?.positions?.active_count || 0}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
      </Row>

      {/* 系统状态 */}
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={16}>
          <Card title="系统状态">
            {summary?.system?.services && (
              <>
                <p>
                  {summary.system.services.backend === 'running' ? (
                    <><CheckCircleOutlined style={{ color: '#52c41a' }} /> 后端服务运行正常</>
                  ) : (
                    <><ExclamationCircleOutlined style={{ color: '#ff4d4f' }} /> 后端服务异常</>
                  )}
                </p>
                <p>
                  {summary.system.services.database === 'running' ? (
                    <><CheckCircleOutlined style={{ color: '#52c41a' }} /> 数据库连接正常</>
                  ) : (
                    <><ExclamationCircleOutlined style={{ color: '#ff4d4f' }} /> 数据库连接异常</>
                  )}
                </p>
                <p>
                  {summary.system.services.redis === 'running' ? (
                    <><CheckCircleOutlined style={{ color: '#52c41a' }} /> Redis缓存正常</>
                  ) : (
                    <><ExclamationCircleOutlined style={{ color: '#ff4d4f' }} /> Redis缓存异常</>
                  )}
                </p>
                <p>
                  {summary.system.services.trading_system === 'running' ? (
                    <><CheckCircleOutlined style={{ color: '#52c41a' }} /> 交易系统运行中</>
                  ) : (
                    <><ExclamationCircleOutlined style={{ color: '#faad14' }} /> 交易系统未启动</>
                  )}
                </p>
              </>
            )}
          </Card>
        </Col>
        <Col xs={24} lg={8}>
          <Card title="数据概览">
            {summary?.system?.data_status && (
              <>
                <p>• 交易对数量: {summary.system.data_status.instruments_count}</p>
                <p>• 特征数量: {summary.system.data_status.features_count}</p>
                <p>• 数据覆盖天数: {summary.system.data_status.date_range_days}</p>
                <p>• 最后更新: {new Date(summary.last_update).toLocaleString()}</p>
              </>
            )}
          </Card>
        </Col>
      </Row>
    </div>
  )
}

export default Dashboard
