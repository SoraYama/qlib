import React, { useEffect } from 'react'
import { Card, Row, Col, Button, Tag, Space, Typography, Alert, Progress } from 'antd'
import {
  ReloadOutlined,
  MergeOutlined,
  CheckCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons'
import { useDispatch, useSelector } from 'react-redux'
import { RootState, AppDispatch } from '../store'
import {
  fetchDataStatus,
  fetchDataQuality,
  fetchInstruments,
  fetchFeatures,
  updateData,
  mergeData
} from '../store/slices/dataSlice'

const { Title, Text } = Typography

const DataManager: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const {
    status,
    quality,
    instruments,
    features,
    updating,
    error
  } = useSelector((state: RootState) => state.data)

  useEffect(() => {
    dispatch(fetchDataStatus())
    dispatch(fetchDataQuality())
    dispatch(fetchInstruments())
    dispatch(fetchFeatures())
  }, [dispatch])

  const handleUpdateData = (type: string) => {
    dispatch(updateData(type))
  }

  const handleMergeData = () => {
    dispatch(mergeData())
  }



  return (
    <div>
      <Title level={2}>数据管理</Title>

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

      {/* 数据状态概览 */}
      <Row gutter={[16, 16]} style={{ marginBottom: 24 }}>
        <Col xs={24} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <CheckCircleOutlined style={{ fontSize: 32, color: '#52c41a', marginBottom: 8 }} />
              <div>
                <Text strong style={{ fontSize: 18 }}>
                  {status?.date_range?.total_days || 0}
                </Text>
                <div>数据覆盖天数</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <CheckCircleOutlined style={{ fontSize: 32, color: '#1890ff', marginBottom: 8 }} />
              <div>
                <Text strong style={{ fontSize: 18 }}>
                  {instruments.length}
                </Text>
                <div>交易对数量</div>
              </div>
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card>
            <div style={{ textAlign: 'center' }}>
              <CheckCircleOutlined style={{ fontSize: 32, color: '#722ed1', marginBottom: 8 }} />
              <div>
                <Text strong style={{ fontSize: 18 }}>
                  {features.length}
                </Text>
                <div>特征数量</div>
              </div>
            </div>
          </Card>
        </Col>
      </Row>

      {/* 数据操作 */}
      <Card title="数据操作" style={{ marginBottom: 24 }}>
        <Space wrap>
          <Button
            type="primary"
            icon={<ReloadOutlined />}
            loading={updating}
            onClick={() => handleUpdateData('price')}
          >
            更新价格数据
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={updating}
            onClick={() => handleUpdateData('onchain')}
          >
            更新链上数据
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={updating}
            onClick={() => handleUpdateData('news')}
          >
            更新新闻数据
          </Button>
          <Button
            icon={<ReloadOutlined />}
            loading={updating}
            onClick={() => handleUpdateData('all')}
          >
            更新所有数据
          </Button>
          <Button
            icon={<MergeOutlined />}
            loading={updating}
            onClick={handleMergeData}
          >
            合并数据
          </Button>
        </Space>
      </Card>

      {/* 数据质量 */}
      <Card title="数据质量" style={{ marginBottom: 24 }}>
        <Row gutter={[16, 16]}>
          <Col xs={24} sm={8}>
            <div>
              <Text>整体质量评分</Text>
              <Progress
                percent={quality?.overall_score ? quality.overall_score * 100 : 85}
                status={quality?.overall_score && quality.overall_score > 0.8 ? 'success' : 'normal'}
              />
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div>
              <Text>缺失数据</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="orange">
                  <ExclamationCircleOutlined /> 少量缺失
                </Tag>
              </div>
            </div>
          </Col>
          <Col xs={24} sm={8}>
            <div>
              <Text>数据一致性</Text>
              <div style={{ marginTop: 8 }}>
                <Tag color="green">
                  <CheckCircleOutlined /> 良好
                </Tag>
              </div>
            </div>
          </Col>
        </Row>
      </Card>

    </div>
  )
}

export default DataManager
