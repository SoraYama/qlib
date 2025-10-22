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
  Tabs,
  Checkbox,
  Tooltip
} from 'antd'
import {
  PlayCircleOutlined,
  BarChartOutlined,
  ThunderboltOutlined,
  InfoCircleOutlined,
  StopOutlined,
  ReloadOutlined
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import {
  fetchModels,
  fetchModelPerformance,
  trainModel,
  tuneHyperparameters,
  compareModels,
  fetchTrainingTasks,
  cancelTrainingTask
} from '../store/slices/modelSlice'
import ModelComparisonRadar from '../components/Charts/ModelComparisonRadar'
import ModelComparisonBar from '../components/Charts/ModelComparisonBar'

const { Title, Text } = Typography
const { Option } = Select
const { TabPane } = Tabs

const ModelTrainer: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    models,
    loading,
    training,
    error,
    taskList
  } = useSelector((state: RootState) => state.model)

  const [selectedModel, setSelectedModel] = useState<string>('')
  const [selectedModelsForComparison, setSelectedModelsForComparison] = useState<string[]>([])
  const [comparisonData, setComparisonData] = useState<any>(null)
  const [comparingModels, setComparingModels] = useState(false)
  const [form] = Form.useForm()
  const [progressInterval, setProgressInterval] = useState<number | null>(null)

  const labelWithTip = (labelText: string, tipText: string) => (
    <span>
      {labelText}
      <Tooltip title={tipText} placement="right">
        <InfoCircleOutlined style={{ marginLeft: 6, color: '#999' }} />
      </Tooltip>
    </span>
  )

  // 参数默认值配置
  const defaultParams = {
    learning_rate: 0.1,
    max_depth: 6,
    num_leaves: 31,
    subsample: 0.8
  }

  useEffect(() => {
    dispatch(fetchModels())
    dispatch(fetchTrainingTasks())
  }, [dispatch])

  // 训练进度轮询 - 使用任务列表API
  useEffect(() => {
    // 检查是否有正在运行的任务
    const hasRunningTasks = taskList.some(task =>
      ['pending', 'running', 'cancelling'].includes(task.status)
    )

    if (hasRunningTasks) {
      const interval = setInterval(() => {
        dispatch(fetchTrainingTasks())
      }, 2000) // 每2秒更新一次
      setProgressInterval(interval)

      return () => {
        clearInterval(interval)
        setProgressInterval(null)
      }
    } else if (progressInterval) {
      clearInterval(progressInterval)
      setProgressInterval(null)
    }
  }, [taskList, dispatch, progressInterval])

  // 组件卸载时清理定时器
  useEffect(() => {
    return () => {
      if (progressInterval) {
        clearInterval(progressInterval)
      }
    }
  }, [progressInterval])

  const handleModelChange = (value: string) => {
    setSelectedModel(value)
    // 获取模型参数，如果没有则使用推荐默认值
    const model = models.find(m => m.name === value)
    if (model && model.default_params) {
      form.setFieldsValue(model.default_params)
    } else {
      // 使用推荐的默认值
      form.setFieldsValue(defaultParams)
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

  const handleCancelTraining = (taskId: string) => {
    dispatch(cancelTrainingTask(taskId)).then(() => {
      // 取消后立即刷新任务列表
      dispatch(fetchTrainingTasks())
    })
  }

  const handleRefreshProgress = () => {
    dispatch(fetchTrainingTasks())
  }

  const handleCompareModels = async () => {
    if (selectedModelsForComparison.length < 2) {
      return
    }
    setComparingModels(true)
    try {
      const result = await dispatch(compareModels(selectedModelsForComparison)).unwrap()
      // 规范化后端返回的数据结构，适配 {model_name, metrics:{...}} 或扁平结构
      const normalize = (arr: any[]) => (arr || []).map((it: any) => {
        const name = it?.model_name || it?.name || it?.model || 'unknown'
        const metrics = it?.metrics || {
          accuracy: it?.accuracy,
          precision: it?.precision,
          recall: it?.recall,
          f1_score: it?.f1_score || it?.f1,
          sharpe_ratio: it?.sharpe_ratio || it?.sharpe,
          max_drawdown: it?.max_drawdown || it?.mdd,
          annual_return: it?.annual_return || it?.annualized_return,
        }
        return { model_name: name, metrics: metrics || {} }
      })
      setComparisonData(normalize(result))
    } catch (error) {
      console.error('模型对比失败:', error)
    } finally {
      setComparingModels(false)
    }
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
                      <Form.Item
                        label={labelWithTip('学习率', '每次参数更新的步长，过大易震荡，过小收敛慢。推荐范围：0.01-0.3，默认：0.1')}
                        name="learning_rate"
                        initialValue={defaultParams.learning_rate}
                      >
                        <InputNumber
                          min={0.001}
                          max={1}
                          step={0.01}
                          style={{ width: '100%' }}
                          placeholder="推荐：0.1"
                        />
                      </Form.Item>
                      <Form.Item
                        label={labelWithTip('最大深度', '决策树最大深度，增大可拟合更复杂模式但易过拟合。推荐范围：3-10，默认：6')}
                        name="max_depth"
                        initialValue={defaultParams.max_depth}
                      >
                        <InputNumber
                          min={3}
                          max={20}
                          style={{ width: '100%' }}
                          placeholder="推荐：6"
                        />
                      </Form.Item>
                      <Form.Item
                        label={labelWithTip('叶子节点数', '树的叶子数量上限，数值越大模型复杂度越高。推荐范围：15-100，默认：31')}
                        name="num_leaves"
                        initialValue={defaultParams.num_leaves}
                      >
                        <InputNumber
                          min={10}
                          max={500}
                          style={{ width: '100%' }}
                          placeholder="推荐：31"
                        />
                      </Form.Item>
                      <Form.Item
                        label={labelWithTip('子样本比例', '每次训练使用的数据子样本比例，有助于降低过拟合。推荐范围：0.6-1.0，默认：0.8')}
                        name="subsample"
                        initialValue={defaultParams.subsample}
                      >
                        <InputNumber
                          min={0.1}
                          max={1}
                          step={0.1}
                          style={{ width: '100%' }}
                          placeholder="推荐：0.8"
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

        <TabPane tab="训练进度" key="2">
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Card
                title="训练任务列表"
                extra={
                  <Button
                    size="small"
                    icon={<ReloadOutlined />}
                    onClick={handleRefreshProgress}
                  >
                    刷新
                  </Button>
                }
              >
                <Table
                  columns={[
                    {
                      title: '任务ID',
                      dataIndex: 'task_id',
                      key: 'task_id',
                      width: 120,
                      render: (id: string) => (
                        <Text style={{ fontFamily: 'monospace', fontSize: 12 }}>
                          {id.substring(0, 8)}...
                        </Text>
                      ),
                    },
                    {
                      title: '模型',
                      dataIndex: 'config',
                      key: 'config',
                      width: 100,
                      render: (config: string) => (
                        <Tag color="blue">{config}</Tag>
                      ),
                    },
                    {
                      title: '状态',
                      dataIndex: 'status',
                      key: 'status',
                      width: 100,
                      render: (status: string) => {
                        const statusConfig = {
                          pending: { color: 'default', text: '等待中' },
                          running: { color: 'processing', text: '训练中' },
                          completed: { color: 'success', text: '已完成' },
                          failed: { color: 'error', text: '失败' },
                          cancelled: { color: 'default', text: '已取消' },
                          cancelling: { color: 'warning', text: '取消中' },
                        }
                        const config = statusConfig[status as keyof typeof statusConfig] || { color: 'default', text: status }
                        return <Tag color={config.color}>{config.text}</Tag>
                      },
                    },
                    {
                      title: '进度',
                      dataIndex: 'progress',
                      key: 'progress',
                      width: 250,
                      render: (progress: number, record: any) => (
                        <div>
                          <Progress
                            percent={progress}
                            size="small"
                            status={
                              record.status === 'completed' ? 'success' :
                              record.status === 'failed' ? 'exception' :
                              record.status === 'cancelled' ? 'exception' :
                              'active'
                            }
                          />
                          <Text type="secondary" style={{ fontSize: 12 }}>
                            {record.current_stage}
                          </Text>
                          {record.error && (
                            <div style={{ marginTop: 4 }}>
                              <Text type="danger" style={{ fontSize: 11 }}>
                                错误: {record.error}
                              </Text>
                            </div>
                          )}
                        </div>
                      ),
                    },
                    {
                      title: '创建时间',
                      dataIndex: 'created_at',
                      key: 'created_at',
                      width: 160,
                      render: (time: string) => (
                        <Text style={{ fontSize: 12 }}>
                          {new Date(time).toLocaleString()}
                        </Text>
                      ),
                    },
                    {
                      title: '更新时间',
                      dataIndex: 'updated_at',
                      key: 'updated_at',
                      width: 160,
                      render: (time: string) => (
                        <Text style={{ fontSize: 12 }}>
                          {new Date(time).toLocaleString()}
                        </Text>
                      ),
                    },
                    {
                      title: '操作',
                      key: 'action',
                      width: 100,
                      render: (_: any, record: any) => (
                        <Space size="small">
                          {record.status === 'running' && (
                            <Button
                              size="small"
                              danger
                              icon={<StopOutlined />}
                              onClick={() => handleCancelTraining(record.task_id)}
                            >
                              取消
                            </Button>
                          )}
                          {['completed', 'failed', 'cancelled'].includes(record.status) && (
                            <Text type="secondary" style={{ fontSize: 12 }}>-</Text>
                          )}
                        </Space>
                      ),
                    },
                  ]}
                  dataSource={taskList}
                  loading={loading}
                  rowKey="task_id"
                  pagination={{
                    pageSize: 10,
                    showSizeChanger: true,
                    showTotal: (total) => `共 ${total} 个任务`,
                  }}
                  locale={{
                    emptyText: (
                      <div style={{ padding: '40px 0' }}>
                        <Text type="secondary">暂无训练任务</Text>
                        <br />
                        <Text type="secondary" style={{ fontSize: 12 }}>
                          请在"模型选择"标签页中启动训练任务
                        </Text>
                      </div>
                    ),
                  }}
                />
              </Card>
            </Col>
          </Row>
        </TabPane>

        <TabPane tab="模型对比" key="3">
          <Row gutter={[16, 16]}>
            <Col xs={24}>
              <Card title="选择对比模型">
                <div style={{ marginBottom: 16 }}>
                  <Text type="secondary">请选择至少2个模型进行对比：</Text>
                </div>
                <Checkbox.Group
                  value={selectedModelsForComparison}
                  onChange={(values) => setSelectedModelsForComparison(values as string[])}
                  style={{ width: '100%' }}
                >
                  <Row>
                    {models.map(model => (
                      <Col xs={24} sm={12} md={8} key={model.name} style={{ marginBottom: 8 }}>
                        <Checkbox value={model.name}>
                          <Tag color="blue">{model.name}</Tag>
                        </Checkbox>
                      </Col>
                    ))}
                  </Row>
                </Checkbox.Group>
                <div style={{ marginTop: 16 }}>
                  <Button
                    type="primary"
                    icon={<BarChartOutlined />}
                    onClick={handleCompareModels}
                    loading={comparingModels}
                    disabled={selectedModelsForComparison.length < 2}
                  >
                    生成对比报告
                  </Button>
                  {selectedModelsForComparison.length < 2 && (
                    <Text type="secondary" style={{ marginLeft: 16 }}>
                      已选择 {selectedModelsForComparison.length} 个模型，至少需要 2 个
                    </Text>
                  )}
                </div>
              </Card>
            </Col>

            {comparisonData && (
              <>
                {/* 性能对比表格 */}
                <Col xs={24}>
                  <Card title="性能指标对比">
                    <Table
                      columns={[
                        {
                          title: '指标',
                          dataIndex: 'metric',
                          key: 'metric',
                          fixed: 'left',
                          width: 120,
                        },
                        ...selectedModelsForComparison.map(modelName => ({
                          title: modelName,
                          dataIndex: modelName,
                          key: modelName,
                          render: (value: number, record: any) => {
                            // 找出该指标的最优值
                            const values = selectedModelsForComparison.map(name => record[name])
                            const maxValue = Math.max(...values)
                            const isMax = value === maxValue
                            return (
                              <Text
                                strong={isMax}
                                style={{
                                  fontFamily: 'monospace',
                                  color: isMax ? '#52c41a' : undefined
                                }}
                              >
                                {typeof value === 'number' ? value.toFixed(4) : value}
                              </Text>
                            )
                          },
                        }))
                      ]}
                      dataSource={[
                        {
                          metric: '准确率',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.accuracy
                            ])
                          )
                        },
                        {
                          metric: '精确率',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.precision
                            ])
                          )
                        },
                        {
                          metric: '召回率',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.recall
                            ])
                          )
                        },
                        {
                          metric: 'F1分数',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.f1_score
                            ])
                          )
                        },
                        {
                          metric: '夏普比率',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.sharpe_ratio
                            ])
                          )
                        },
                        {
                          metric: '最大回撤',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.max_drawdown
                            ])
                          )
                        },
                        {
                          metric: '年化收益',
                          ...Object.fromEntries(
                            comparisonData.map((item: any) => [
                              item.model_name,
                              item.metrics.annual_return
                            ])
                          )
                        }
                      ]}
                      rowKey="metric"
                      pagination={false}
                      scroll={{ x: true }}
                    />
                  </Card>
                </Col>

                {/* 雷达图 */}
                <Col xs={24} lg={12}>
                  <Card title="多维度性能对比">
                    <ModelComparisonRadar
                      data={comparisonData}
                      loading={comparingModels}
                      height={500}
                    />
                  </Card>
                </Col>

                {/* 柱状图 */}
                <Col xs={24} lg={12}>
                  <Card title="指标对比">
                    <ModelComparisonBar
                      data={comparisonData}
                      loading={comparingModels}
                      height={500}
                    />
                  </Card>
                </Col>
              </>
            )}
          </Row>
        </TabPane>
      </Tabs>
    </div>
  )
}

export default ModelTrainer
