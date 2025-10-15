import React, { useEffect } from 'react'
import {
  Card,
  Row,
  Col,
  Form,
  Input,
  InputNumber,
  Select,
  Button,
  Table,
  Tag,
  Space,
  Typography,
  Alert,
  DatePicker,
  Tabs
} from 'antd'
import {
  PlayCircleOutlined,
  BarChartOutlined,
  DownloadOutlined,
  DeleteOutlined,
  EyeOutlined
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import {
  fetchBacktests,
  runBacktest,
  fetchBacktestResult,
  deleteBacktest
} from '../store/slices/backtestSlice'
import { fetchModels } from '../store/slices/modelSlice'
import dayjs from 'dayjs'

const { Title, Text } = Typography
const { Option } = Select
const { RangePicker } = DatePicker
const { TabPane } = Tabs

const BacktestPanel: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    results,
    loading,
    running,
    error
  } = useSelector((state: RootState) => state.backtest)
  const { models } = useSelector((state: RootState) => state.model)

  const [form] = Form.useForm()

  useEffect(() => {
    dispatch(fetchBacktests())
    dispatch(fetchModels())
  }, [dispatch])

  const handleRunBacktest = () => {
    const values = form.getFieldsValue()
    const config = {
      start_date: values.dateRange[0].format('YYYY-MM-DD'),
      end_date: values.dateRange[1].format('YYYY-MM-DD'),
      initial_capital: values.initial_capital,
      transaction_cost: values.transaction_cost,
      model_name: values.model_name,
      strategy_name: values.strategy_name || 'default_strategy',
    }
    dispatch(runBacktest(config))
  }

  const handleViewResult = (resultId: string) => {
    dispatch(fetchBacktestResult(resultId))
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
      render: (value: number) => (
        <Text style={{ color: value >= 0 ? '#52c41a' : '#ff4d4f' }}>
          {(value * 100).toFixed(2)}%
        </Text>
      ),
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
      render: (value: number) => (
        <Text style={{ color: '#ff4d4f' }}>
          {(value * 100).toFixed(2)}%
        </Text>
      ),
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

      <Tabs defaultActiveKey="1">
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
          <Card title="回测结果分析">
            <div style={{ textAlign: 'center', padding: '40px 0' }}>
              <Text type="secondary">请先选择一个回测结果进行分析</Text>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default BacktestPanel
