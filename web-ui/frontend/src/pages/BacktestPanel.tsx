import {
  BarChartOutlined,
  DeleteOutlined,
  DownloadOutlined,
  EyeOutlined,
  PlayCircleOutlined
} from '@ant-design/icons'
import {
  Alert,
  Button,
  Card,
  Col,
  DatePicker,
  Form,
  Input,
  InputNumber,
  Row,
  Select,
  Space,
  Spin,
  Statistic,
  Table,
  Tabs,
  Tag,
  Typography,
  message
} from 'antd'
import dayjs from 'dayjs'
import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import EquityCurveChart from '../components/Charts/EquityCurveChart'
import { AppDispatch, RootState } from '../store'
import {
  deleteBacktest,
  fetchBacktestMetrics,
  fetchBacktestResult,
  fetchBacktests,
  runBacktest
} from '../store/slices/backtestSlice'
import { fetchModels } from '../store/slices/modelSlice'

const { Title, Text } = Typography
const { Option } = Select
const { RangePicker } = DatePicker
const { TabPane } = Tabs

const BacktestPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    results,
    currentResult,
    metrics,
    loading,
    running,
    error
  } = useSelector((state: RootState) => state.backtest)
  const { models } = useSelector((state: RootState) => state.model)

  const [form] = Form.useForm()
  const [activeTab, setActiveTab] = useState('1')

  useEffect(() => {
    dispatch(fetchBacktests())
    dispatch(fetchModels())
  }, [dispatch])

  const handleRunBacktest = async () => {
    const values = form.getFieldsValue()

    // 验证必填字段
    if (!values.dateRange || !Array.isArray(values.dateRange) || values.dateRange.length !== 2) {
      message.error('请选择有效的时间范围')
      return
    }

    if (!values.model_name) {
      message.error('请选择模型')
      return
    }

    if (!values.initial_capital) {
      message.error('请输入初始资金')
      return
    }

    if (values.transaction_cost === undefined || values.transaction_cost === null) {
      message.error('请输入交易成本')
      return
    }

    try {
      const config = {
        start_date: values.dateRange[0].format('YYYY-MM-DD'),
        end_date: values.dateRange[1].format('YYYY-MM-DD'),
        initial_capital: values.initial_capital,
        transaction_cost: values.transaction_cost,
        model_name: values.model_name,
        strategy_name: values.strategy_name || 'default_strategy',
      }

      const result = await dispatch(runBacktest(config)).unwrap()

      // 如果回测成功，自动获取指标并切换到结果分析页面
      if (result && result.id) {
        dispatch(fetchBacktestMetrics(result.id))
        setActiveTab('3')
        message.success('回测运行成功！')
      }
    } catch (error) {
      console.error('运行回测时发生错误:', error)
      message.error('运行回测时发生错误，请检查输入参数')
    }
  }

  const handleViewResult = (resultId: string) => {
    dispatch(fetchBacktestResult(resultId))
    dispatch(fetchBacktestMetrics(resultId))
    setActiveTab('3') // 切换到结果分析标签页
  }

  const handleDeleteResult = (resultId: string) => {
    dispatch(deleteBacktest(resultId))
  }

  const resultColumns = [
    {
      title: '回测ID',
      dataIndex: 'id',
      key: 'id',
      render: (id: string) => (
        <Text code>{id}</Text>
      ),
    },
    {
      title: '模型',
      dataIndex: ['config', 'model_name'],
      key: 'model_name',
      render: (name: string) => (
        <Tag color="blue">{name}</Tag>
      ),
    },
    {
      title: '时间范围',
      key: 'date_range',
      render: (_: any, record: any) => (
        <Text>
          {record.config.start_date} ~ {record.config.end_date}
        </Text>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => {
        const color = status === 'completed' ? 'green' :
                     status === 'running' ? 'blue' : 'red'
        const text = status === 'completed' ? '已完成' :
                    status === 'running' ? '运行中' : '失败'
        return <Tag color={color}>{text}</Tag>
      },
    },
    {
      title: '总收益',
      dataIndex: ['metrics', 'total_return'],
      key: 'total_return',
      render: (value: number) => {
        const returnValue = value || 0
        return (
          <Text style={{ color: returnValue >= 0 ? '#52c41a' : '#ff4d4f' }}>
            {(returnValue * 100).toFixed(2)}%
          </Text>
        )
      },
    },
    {
      title: '夏普比率',
      dataIndex: ['metrics', 'sharpe_ratio'],
      key: 'sharpe_ratio',
      render: (value: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {value?.toFixed(3) || '-'}
        </Text>
      ),
    },
    {
      title: '最大回撤',
      dataIndex: ['metrics', 'max_drawdown'],
      key: 'max_drawdown',
      render: (value: number) => {
        const drawdownValue = value || 0
        return (
          <Text style={{ color: '#ff4d4f' }}>
            {(drawdownValue * 100).toFixed(2)}%
          </Text>
        )
      },
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => dayjs(date).format('YYYY-MM-DD HH:mm'),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            icon={<EyeOutlined />}
            onClick={() => handleViewResult(record.id)}
          >
            查看
          </Button>
          <Button
            type="link"
            size="small"
            icon={<DownloadOutlined />}
          >
            导出
          </Button>
          <Button
            type="link"
            size="small"
            danger
            icon={<DeleteOutlined />}
            onClick={() => handleDeleteResult(record.id)}
          >
            删除
          </Button>
        </Space>
      ),
    },
  ]


  return (
    <div>
      <Title level={2}>回测分析</Title>

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

      <Tabs activeKey={activeTab} onChange={setActiveTab}>
        <TabPane tab="运行回测" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="回测配置">
                <Form form={form} layout="vertical">
                  <Form.Item
                    label="时间范围"
                    name="dateRange"
                    rules={[{ required: true, message: '请选择时间范围' }]}
                  >
                    <RangePicker
                      style={{ width: '100%' }}
                      defaultValue={[dayjs().subtract(6, 'month'), dayjs()]}
                    />
                  </Form.Item>

                  <Form.Item
                    label="模型"
                    name="model_name"
                    rules={[{ required: true, message: '请选择模型' }]}
                  >
                    <Select placeholder="请选择模型">
                      {models.map(model => (
                        <Option key={model.name} value={model.name}>
                          {model.name}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>

                  <Form.Item
                    label="策略名称"
                    name="strategy_name"
                    initialValue="default_strategy"
                  >
                    <Input placeholder="请输入策略名称" />
                  </Form.Item>

                  <Form.Item
                    label="初始资金"
                    name="initial_capital"
                    initialValue={100000}
                    rules={[{ required: true, message: '请输入初始资金' }]}
                  >
                    <InputNumber
                      min={1000}
                      max={10000000}
                      style={{ width: '100%' }}
                      formatter={value => `¥ ${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}
                      parser={value => value!.replace(/¥\s?|(,*)/g, '') as any}
                    />
                  </Form.Item>

                  <Form.Item
                    label="交易成本"
                    name="transaction_cost"
                    initialValue={0.001}
                    rules={[{ required: true, message: '请输入交易成本' }]}
                  >
                    <InputNumber
                      min={0}
                      max={0.01}
                      step={0.0001}
                      style={{ width: '100%' }}
                      formatter={value => `${(value! * 100).toFixed(2)}%`}
                      parser={value => parseFloat(value!.replace('%', '')) / 100 as any}
                    />
                  </Form.Item>

                  <Form.Item>
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      loading={running}
                      onClick={handleRunBacktest}
                      size="large"
                      block
                    >
                      运行回测
                    </Button>
                  </Form.Item>
                </Form>
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="回测说明">
                <div style={{ marginBottom: 16 }}>
                  <Text strong>回测参数说明：</Text>
                </div>
                <ul>
                  <li><Text>时间范围：选择回测的时间段</Text></li>
                  <li><Text>模型：选择用于预测的机器学习模型</Text></li>
                  <li><Text>初始资金：回测开始时的资金数量</Text></li>
                  <li><Text>交易成本：每次交易的手续费比例</Text></li>
                </ul>

                <div style={{ marginTop: 24 }}>
                  <Text strong>注意事项：</Text>
                </div>
                <ul>
                  <li><Text>回测结果仅供参考，不保证实盘表现</Text></li>
                  <li><Text>建议使用较长时间段的数据进行回测</Text></li>
                  <li><Text>回测过程中请勿关闭页面</Text></li>
                </ul>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="回测结果" key="2">
          <Card
            title="回测历史"
            extra={
              <Button
                icon={<BarChartOutlined />}
                onClick={() => dispatch(fetchBacktests())}
                loading={loading}
              >
                刷新
              </Button>
            }
          >
            <Table
              columns={resultColumns}
              dataSource={results}
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

        <TabPane tab="结果分析" key="3">
          {!currentResult ? (
            <Card title="回测结果分析">
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Text type="secondary">请先选择一个回测结果进行分析</Text>
              </div>
            </Card>
          ) : !currentResult.metrics ? (
            <Card title="回测结果分析">
              <div style={{ textAlign: 'center', padding: '40px 0' }}>
                <Spin size="large" />
                <div style={{ marginTop: 16 }}>
                  <Text type="secondary">正在加载回测指标...</Text>
                </div>
              </div>
            </Card>
          ) : (
            <>
              {/* 关键指标卡片 */}
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="总收益"
                      value={(currentResult.metrics?.total_return || 0) * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: (currentResult.metrics?.total_return || 0) >= 0 ? '#3f8600' : '#cf1322'
                      }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="年化收益"
                      value={(currentResult.metrics?.annual_return || 0) * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{
                        color: (currentResult.metrics?.annual_return || 0) >= 0 ? '#3f8600' : '#cf1322'
                      }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="夏普比率"
                      value={currentResult.metrics?.sharpe_ratio || 0}
                      precision={3}
                      valueStyle={{ color: '#1890ff' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="最大回撤"
                      value={Math.abs(currentResult.metrics?.max_drawdown || 0) * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: '#cf1322' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="胜率"
                      value={(currentResult.metrics?.win_rate || 0) * 100}
                      precision={2}
                      suffix="%"
                      valueStyle={{ color: '#52c41a' }}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} lg={8}>
                  <Card>
                    <Statistic
                      title="盈亏比"
                      value={currentResult.metrics?.profit_factor || 0}
                      precision={2}
                      valueStyle={{ color: '#722ed1' }}
                    />
                  </Card>
                </Col>
              </Row>

              {/* 收益曲线图 */}
              <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
                <Col xs={24}>
                  <Card title="收益曲线">
                    {loading || !metrics?.equity_curve ? (
                      <div style={{ textAlign: 'center', padding: '100px 0' }}>
                        <Spin size="large" />
                      </div>
                    ) : (
                      <EquityCurveChart
                        data={metrics.equity_curve}
                        loading={loading}
                        height={400}
                      />
                    )}
                  </Card>
                </Col>
              </Row>

              {/* 交易记录表格 */}
              <Row gutter={[16, 16]}>
                <Col xs={24}>
                  <Card title="交易记录">
                    {loading || !metrics?.trades ? (
                      <div style={{ textAlign: 'center', padding: '40px 0' }}>
                        <Spin size="large" />
                      </div>
                    ) : (
                      <Table
                        columns={[
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
                              <Tag color={side === 'buy' ? 'green' : 'red'}>
                                {side === 'buy' ? '买入' : '卖出'}
                              </Tag>
                            ),
                          },
                          {
                            title: '入场价格',
                            dataIndex: 'entry_price',
                            key: 'entry_price',
                            render: (price: number) => (
                              <Text style={{ fontFamily: 'monospace' }}>
                                ${price?.toFixed(2)}
                              </Text>
                            ),
                          },
                          {
                            title: '出场价格',
                            dataIndex: 'exit_price',
                            key: 'exit_price',
                            render: (price: number) => (
                              <Text style={{ fontFamily: 'monospace' }}>
                                {price ? `$${price.toFixed(2)}` : '-'}
                              </Text>
                            ),
                          },
                          {
                            title: '数量',
                            dataIndex: 'amount',
                            key: 'amount',
                            render: (amount: number) => (
                              <Text style={{ fontFamily: 'monospace' }}>
                                {amount?.toFixed(6)}
                              </Text>
                            ),
                          },
                          {
                            title: '盈亏',
                            dataIndex: 'pnl',
                            key: 'pnl',
                            render: (pnl: number) => (
                              <Text
                                style={{
                                  fontFamily: 'monospace',
                                  color: pnl >= 0 ? '#52c41a' : '#ff4d4f'
                                }}
                              >
                                {pnl >= 0 ? '+' : ''}${pnl?.toFixed(2)}
                              </Text>
                            ),
                          },
                          {
                            title: '入场时间',
                            dataIndex: 'entry_time',
                            key: 'entry_time',
                            render: (time: string) => dayjs(time).format('YYYY-MM-DD HH:mm'),
                          },
                          {
                            title: '出场时间',
                            dataIndex: 'exit_time',
                            key: 'exit_time',
                            render: (time: string) =>
                              time ? dayjs(time).format('YYYY-MM-DD HH:mm') : '-',
                          },
                        ]}
                        dataSource={metrics.trades}
                        rowKey={(record, index) => `${record.symbol}_${index}`}
                        pagination={{
                          pageSize: 10,
                          showSizeChanger: true,
                          showQuickJumper: true,
                          showTotal: (total, range) =>
                            `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
                        }}
                      />
                    )}
                  </Card>
                </Col>
              </Row>
            </>
          )}
        </TabPane>
      </Tabs>
    </div>
  )
}

export default BacktestPanel
