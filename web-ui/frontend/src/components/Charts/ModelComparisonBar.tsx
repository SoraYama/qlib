import React from 'react'
import ReactECharts from 'echarts-for-react'
import { Spin } from 'antd'

interface ModelComparisonData {
  model_name: string
  metrics: {
    accuracy?: number
    precision?: number
    recall?: number
    f1_score?: number
    sharpe_ratio?: number
    max_drawdown?: number
    annual_return?: number
  }
}

interface ModelComparisonBarProps {
  data: ModelComparisonData[]
  loading?: boolean
  height?: number
}

const ModelComparisonBar: React.FC<ModelComparisonBarProps> = ({
  data,
  loading = false,
  height = 400
}) => {
  // 颜色列表
  const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#eb2f96']

  // 指标列表
  const metrics = [
    { key: 'accuracy', name: '准确率' },
    { key: 'precision', name: '精确率' },
    { key: 'recall', name: '召回率' },
    { key: 'f1_score', name: 'F1分数' },
    { key: 'sharpe_ratio', name: '夏普比率' },
    { key: 'annual_return', name: '年化收益' }
  ]

  // 构建系列数据
  const series = (data || []).map((item, index) => ({
    name: item.model_name,
    type: 'bar',
    data: metrics.map(metric => {
      const value = (item.metrics?.[metric.key as keyof typeof item.metrics]) as number | undefined
      return value !== undefined ? value : 0
    }),
    itemStyle: {
      color: colors[index % colors.length]
    },
    label: {
      show: false
    }
  }))

  const option = {
    title: {
      text: '模型性能对比',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      },
      formatter: (params: any) => {
        let result = `<div><strong>${params[0].axisValue}</strong></div>`
        params.forEach((param: any) => {
          result += `<div>${param.marker} ${param.seriesName}: ${param.value.toFixed(4)}</div>`
        })
        return result
      }
    },
    legend: {
      bottom: 10,
      data: data.map(item => item.model_name)
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '15%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: metrics.map(m => m.name),
      axisLabel: {
        rotate: 30
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => value.toFixed(2)
      }
    },
    series: series
  }

  if (loading) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#999' }}>暂无数据</div>
      </div>
    )
  }

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export default ModelComparisonBar

