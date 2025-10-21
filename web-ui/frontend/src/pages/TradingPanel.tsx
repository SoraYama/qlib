import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Button,
  Table,
  Tag,
  Space,
  Typography,
  Alert,
  Statistic,
  Form,
  InputNumber,
  Modal,
  Tabs
} from 'antd'
import {
  PlayCircleOutlined,
  PauseCircleOutlined,
  SettingOutlined,
  DollarOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import {
  fetchTradingStatus,
  startTrading,
  stopTrading,
  fetchPositions,
  fetchOrders,
  updateRiskLimits,
  fetchKline,
  fetchTradingPlan
} from '../store/slices/tradingSlice'
import { fetchModels } from '../store/slices/modelSlice'
import KlineChart from '../components/Charts/KlineChart'

const { Title, Text } = Typography
const { TabPane } = Tabs

const TradingPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    status,
    positions,
    orders,
    kline,
    plan,
    loading,
    starting,
    stopping,
    error
  } = useSelector((state: RootState) => state.trading)

  const [riskModalVisible, setRiskModalVisible] = useState(false)
  const [form] = Form.useForm()

  useEffect(() => {
    dispatch(fetchTradingStatus())
    dispatch(fetchPositions())
    dispatch(fetchOrders())
    dispatch(fetchModels())
    dispatch(fetchKline({ symbol: 'BTC_USDT', interval: '1m', limit: 200 }))
    dispatch(fetchTradingPlan())
  }, [dispatch])

  // 定时刷新 K 线与计划
  useEffect(() => {
    const timer = setInterval(() => {
      dispatch(fetchKline({ symbol: 'BTC_USDT', interval: '1m', limit: 200 }))
      dispatch(fetchTradingPlan())
      dispatch(fetchTradingStatus())
    }, 20_000)
    return () => clearInterval(timer)
  }, [dispatch])

  const handleStartTrading = () => {
    const config = {
      strategy_name: 'default_strategy',
      risk_limits: status?.risk_limits || {}
    }
    dispatch(startTrading(config))
  }

  const handleStopTrading = () => {
    dispatch(stopTrading())
  }

  const handleUpdateRiskLimits = () => {
    const values = form.getFieldsValue()
    dispatch(updateRiskLimits(values))
    setRiskModalVisible(false)
  }

  const positionColumns = [
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Text strong style={{ fontFamily: 'monospace' }}>
          {symbol}
        </Text>
      ),
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '多头' : '空头'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {size.toFixed(6)}
        </Text>
      ),
    },
    {
      title: '入场价格',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          ${price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          ${price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '未实现盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      render: (pnl: number) => (
        <Text
          style={{
            fontFamily: 'monospace',
            color: pnl >= 0 ? '#52c41a' : '#ff4d4f'
          }}
        >
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </Text>
      ),
    },
  ]

  const orderColumns = [
    {
      title: '订单ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Text code>{id.substring(0, 8)}...</Text>
      ),
    },
    {
      title: '交易对',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol: string) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {symbol}
        </Text>
      ),
    },
    {
      title: '方向',
      dataIndex: 'side',
      key: 'side',
      render: (side: string) => (
        <Tag color={side === 'buy' ? 'green' : 'red'}>
          {side === 'buy' ? '买入' : '卖出'}
        </Tag>
      ),
    },
    {
      title: '类型',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => (
        <Tag>{type === 'market' ? '市价' : '限价'}</Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'amount',
      key: 'amount',
      render: (amount: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {amount.toFixed(6)}
        </Text>
      ),
    },
    {
      title: '价格',
      dataIndex: 'price',
      key: 'price',
      render: (price: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {price ? `$${price.toFixed(2)}` : '-'}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'filled' ? 'green' :
                     status === 'pending' ? 'blue' :
                     status === 'cancelled' ? 'orange' : 'red'
        const text = status === 'filled' ? '已成交' :
                    status === 'pending' ? '待成交' :
                    status === 'cancelled' ? '已取消' : '已拒绝'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleString(),
    },
  ]


  return (
    <div>
      <Title level={2}>实盘交易</Title>

      {error && (
        <Alert
          message="操作失败"
          description={error}
          type="error"
          showIcon
          closable
          style={{ marginBottom: 24 }}
        />
      )}

      {/* 交易状态卡片 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="交易状态"
              value={status?.is_running ? '运行中' : '已停止'}
              prefix={status?.is_running ? <PlayCircleOutlined /> : <PauseCircleOutlined />}
              valueStyle={{ color: status?.is_running ? '#52c41a' : '#ff4d4f' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="总资产"
              value={status?.account_info?.total_balance || 0}
              precision={2}
              prefix={<DollarOutlined />}
              valueStyle={{ color: '#3f8600' }}
            />
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <Statistic
              title="今日盈亏"
              value={status?.account_info?.daily_pnl || 0}
              precision={2}
              prefix={status?.account_info?.daily_pnl && status.account_info.daily_pnl >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
              valueStyle={{
                color: status?.account_info?.daily_pnl && status.account_info.daily_pnl >= 0 ? '#3f8600' : '#cf1322'
              }}
            />
          </Card>
        </Col>
      </Row>

      {/* 交易控制 */}
      <Card title="交易控制" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]} align="middle">
          <Col xs={24} sm={12}>
            <Space>
              <Button
                type="primary"
                icon={<PlayCircleOutlined />}
                loading={starting}
                onClick={handleStartTrading}
                disabled={status?.is_running}
              >
                启动交易
              </Button>
              <Button
                danger
                icon={<PauseCircleOutlined />}
                loading={stopping}
                onClick={handleStopTrading}
                disabled={!status?.is_running}
              >
                停止交易
              </Button>
            </Space>
          </Col>
          <Col xs={24} sm={12} style={{ textAlign: 'right' }}>
            <Button
              icon={<SettingOutlined />}
              onClick={() => setRiskModalVisible(true)}
            >
              风险设置
            </Button>
          </Col>
        </Row>
      </Card>

      {/* 详细数据 */}
      <Tabs defaultActiveKey="1">
        <TabPane tab="持仓管理" key="1">
          <Card title="当前持仓">
            <div style={{ marginBottom: 16 }}>
              <KlineChart data={kline} plan={plan?.plan} title={`实时K线 ${plan?.plan?.symbol || 'BTC_USDT'}（${status?.is_running ? '实盘运行中' : '未运行'}）`} />
            </div>
            <Table
              columns={positionColumns}
              dataSource={positions}
              loading={loading}
              rowKey="symbol"
              pagination={false}
              locale={{
                emptyText: '暂无持仓'
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="订单历史" key="2">
          <Card title="订单历史">
            <Table
              columns={orderColumns}
              dataSource={orders}
              loading={loading}
              rowKey="id"
              pagination={{
                pageSize: 10,
                showSizeChanger: true,
                showQuickJumper: true,
                showTotal: (total, range) =>
                  `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
              }}
            />
          </Card>
        </TabPane>

        <TabPane tab="风险监控" key="3">
          <Row gutter={[16, 16]}>
            <Col xs={24} sm={8}>
              <Card title="最大仓位限制">
                <Statistic
                  title="单币种最大仓位"
                  value={status?.risk_limits?.max_position_size || 0.3}
                  suffix="%"
                  valueStyle={{ color: '#1890ff' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card title="最大回撤限制">
                <Statistic
                  title="最大回撤"
                  value={status?.risk_limits?.max_drawdown || 0.2}
                  suffix="%"
                  valueStyle={{ color: '#faad14' }}
                />
              </Card>
            </Col>
            <Col xs={24} sm={8}>
              <Card title="止损设置">
                <Statistic
                  title="止损线"
                  value={status?.risk_limits?.stop_loss || 0.05}
                  suffix="%"
                  valueStyle={{ color: '#ff4d4f' }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>
      </Tabs>

      {/* 风险设置模态框 */}
      <Modal
        title="风险设置"
        open={riskModalVisible}
        onOk={handleUpdateRiskLimits}
        onCancel={() => setRiskModalVisible(false)}
        okText="保存"
        cancelText="取消"
      >
        <Form form={form} layout="vertical" initialValues={status?.risk_limits}>
          <Form.Item
            label="单币种最大仓位 (%)"
            name="max_position_size"
            rules={[{ required: true, message: '请输入最大仓位限制' }]}
          >
            <InputNumber
              min={0.01}
              max={1}
              step={0.01}
              style={{ width: '100%' }}
              formatter={value => `${(value! * 100).toFixed(0)}%`}
              parser={value => parseFloat(value!.replace('%', '')) / 100 as any}
            />
          </Form.Item>

          <Form.Item
            label="最大回撤限制 (%)"
            name="max_drawdown"
            rules={[{ required: true, message: '请输入最大回撤限制' }]}
          >
            <InputNumber
              min={0.01}
              max={0.5}
              step={0.01}
              style={{ width: '100%' }}
              formatter={value => `${(value! * 100).toFixed(0)}%`}
              parser={value => parseFloat(value!.replace('%', '')) / 100 as any}
            />
          </Form.Item>

          <Form.Item
            label="止损线 (%)"
            name="stop_loss"
            rules={[{ required: true, message: '请输入止损线' }]}
          >
            <InputNumber
              min={0.01}
              max={0.2}
              step={0.01}
              style={{ width: '100%' }}
              formatter={value => `${(value! * 100).toFixed(0)}%`}
              parser={value => parseFloat(value!.replace('%', '')) / 100 as any}
            />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default TradingPanel
