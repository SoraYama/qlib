import React, { useEffect, useState } from 'react'
import {
  Card,
  Row,
  Col,
  Select,
  Button,
  Form,
  InputNumber,
  Table,
  Tag,
  Space,
  Typography,
  Alert,
  Progress,
  Tabs
} from 'antd'
import {
  PlayCircleOutlined,
  BarChartOutlined,
  ThunderboltOutlined
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import {
  fetchModels,
  fetchModelPerformance,
  trainModel,
  tuneHyperparameters,
  compareModels
} from '../store/slices/modelSlice'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

const ModelTrainer: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    models,
    performance,
    loading,
    training,
    error
  } = useSelector((state: RootState) => state.model)

  const [selectedModel, setSelectedModel] = useState<string>('')
  const [form] = Form.useForm()

  useEffect(() => {
    dispatch(fetchModels())
  }, [dispatch])

  const handleModelChange = (value: string) => {
    setSelectedModel(value)
    // 获取模型参数
    const model = models.find(m => m.name === value)
    if (model) {
      form.setFieldsValue(model.default_params)
    }
    // 获取模型性能数据
    if (value) {
      dispatch(fetchModelPerformance(value))
    }
  }

  const handleTrain = () => {
    const params = form.getFieldsValue()
    dispatch(trainModel({ modelName: selectedModel, params }))
  }

  const handleTune = () => {
    dispatch(tuneHyperparameters({ modelName: selectedModel }))
  }

  const modelColumns = [
    {
      title: '模型名称',
      dataIndex: 'name',
      key: 'name',
      render: (name: string) => (
        <Text strong style={{ fontFamily: 'monospace' }}>
          {name}
        </Text>
      ),
    },
    {
      title: '类型',
      dataIndex: 'class',
      key: 'class',
      render: (type: string) => (
        <Tag color="blue">{type}</Tag>
      ),
    },
    {
      title: '描述',
      dataIndex: 'description',
      key: 'description',
    },
    {
      title: '可调参数',
      dataIndex: 'tunable_params',
      key: 'tunable_params',
      render: (params: string[]) => params.length,
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => setSelectedModel(record.name)}
          >
            选择
          </Button>
        </Space>
      ),
    },
  ]

  const performanceColumns = [
    {
      title: '指标',
      dataIndex: 'metric',
      key: 'metric',
    },
    {
      title: '数值',
      dataIndex: 'value',
      key: 'value',
      render: (value: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {typeof value === 'number' ? value.toFixed(4) : value}
        </Text>
      ),
    },
  ]


  return (
    <div>
      <Title level={2}>模型训练</Title>

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
        <TabPane tab="模型选择" key="1">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={16}>
              <Card title="可用模型">
                <Table
                  columns={modelColumns}
                  dataSource={models}
                  loading={loading}
                  rowKey="name"
                  pagination={false}
                />
              </Card>
            </Col>
            <Col xs={24} lg={8}>
              <Card title="模型配置">
                <Form form={form} layout="vertical">
                  <Form.Item label="选择模型" required>
                    <Select
                      placeholder="请选择模型"
                      value={selectedModel}
                      onChange={handleModelChange}
                    >
                      {models.map(model => (
                        <Option key={model.name} value={model.name}>
                          {model.name}
                        </Option>
                      ))}
                    </Select>
                  </Form.Item>

                  {selectedModel && (
                    <>
                      <Form.Item label="学习率" name="learning_rate">
                        <InputNumber
                          min={0.001}
                          max={1}
                          step={0.01}
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                      <Form.Item label="最大深度" name="max_depth">
                        <InputNumber
                          min={3}
                          max={20}
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                      <Form.Item label="叶子节点数" name="num_leaves">
                        <InputNumber
                          min={10}
                          max={500}
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                      <Form.Item label="子样本比例" name="subsample">
                        <InputNumber
                          min={0.1}
                          max={1}
                          step={0.1}
                          style={{ width: '100%' }}
                        />
                      </Form.Item>
                    </>
                  )}

                  <Space style={{ width: '100%', marginTop: 16 }}>
                    <Button
                      type="primary"
                      icon={<PlayCircleOutlined />}
                      loading={training}
                      onClick={handleTrain}
                      disabled={!selectedModel}
                    >
                      训练模型
                    </Button>
                    <Button
                      icon={<ThunderboltOutlined />}
                      loading={training}
                      onClick={handleTune}
                      disabled={!selectedModel}
                    >
                      超参数调优
                    </Button>
                  </Space>
                </Form>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="性能评估" key="2">
          <Row gutter={[16, 16]}>
            <Col xs={24} lg={12}>
              <Card title="模型性能指标">
                {!selectedModel ? (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Text type="secondary">请先选择一个模型查看性能指标</Text>
                  </div>
                ) : !performance ? (
                  <div style={{ textAlign: 'center', padding: '40px 0' }}>
                    <Text type="secondary">暂无性能数据</Text>
                  </div>
                ) : (
                  <Table
                    columns={performanceColumns}
                    dataSource={[
                      { metric: '准确率', value: performance.accuracy },
                      { metric: '精确率', value: performance.precision },
                      { metric: '召回率', value: performance.recall },
                      { metric: 'F1分数', value: performance.f1_score },
                      { metric: '夏普比率', value: performance.sharpe_ratio },
                      { metric: '最大回撤', value: performance.max_drawdown },
                      { metric: '年化收益', value: performance.annual_return },
                    ]}
                    loading={loading}
                    rowKey="metric"
                    pagination={false}
                    size="small"
                  />
                )}
              </Card>
            </Col>
            <Col xs={24} lg={12}>
              <Card title="训练进度">
                <div style={{ marginBottom: 16 }}>
                  <Text>当前训练进度</Text>
                  <Progress
                    percent={training ? 65 : 0}
                    status={training ? 'active' : 'normal'}
                  />
                </div>
                <div>
                  <Text>超参数调优进度</Text>
                  <Progress
                    percent={training ? 45 : 0}
                    status={training ? 'active' : 'normal'}
                  />
                </div>
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="模型对比" key="3">
          <Card title="模型性能对比">
            <Button
              type="primary"
              icon={<BarChartOutlined />}
              onClick={() => dispatch(compareModels())}
              loading={loading}
            >
              生成对比报告
            </Button>
            <div style={{ marginTop: 16 }}>
              <Text type="secondary">模型对比功能开发中...</Text>
            </div>
          </Card>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default ModelTrainer
