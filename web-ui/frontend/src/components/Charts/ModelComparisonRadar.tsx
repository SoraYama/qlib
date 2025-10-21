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
    annual_return?: number
  }
}

interface ModelComparisonRadarProps {
  data: ModelComparisonData[]
  loading?: boolean
  height?: number
}

const ModelComparisonRadar: React.FC<ModelComparisonRadarProps> = ({
  data,
  loading = false,
  height = 500
}) => {
  // 定义雷达图的指标
  const indicators = [
    { name: '准确率', max: 1 },
    { name: '精确率', max: 1 },
    { name: '召回率', max: 1 },
    { name: 'F1分数', max: 1 },
    { name: '夏普比率', max: 3 },
    { name: '年化收益', max: 1 }
  ]

  // 颜色列表
  const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#eb2f96']

  // 转换数据格式
  const series = (data || []).map((item, index) => ({
    name: item.model_name,
    type: 'radar',
    data: [
      {
        value: [
          (item.metrics?.accuracy ?? 0),
          (item.metrics?.precision ?? 0),
          (item.metrics?.recall ?? 0),
          (item.metrics?.f1_score ?? 0),
          (item.metrics?.sharpe_ratio ?? 0),
          (item.metrics?.annual_return ?? 0)
        ],
        name: item.model_name,
        lineStyle: {
          color: colors[index % colors.length],
          width: 2
        },
        areaStyle: {
          color: colors[index % colors.length],
          opacity: 0.1
        }
      }
    ]
  }))

  const option = {
    title: {
      text: '模型性能雷达图',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'item',
      formatter: (params: any) => {
        const indicatorNames = indicators.map(i => i.name)
        let result = `<div><strong>${params.name}</strong></div>`
        params.value.forEach((val: number, idx: number) => {
          result += `<div>${indicatorNames[idx]}: ${val.toFixed(4)}</div>`
        })
        return result
      }
    },
    legend: {
      bottom: 10,
      data: data.map(item => item.model_name)
    },
    radar: {
      indicator: indicators,
      radius: '60%',
      center: ['50%', '50%'],
      splitNumber: 4,
      splitArea: {
        areaStyle: {
          color: ['rgba(114, 172, 209, 0.05)', 'rgba(114, 172, 209, 0.1)'],
          shadowColor: 'rgba(0, 0, 0, 0.2)',
          shadowBlur: 10
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
      },
      splitLine: {
        lineStyle: {
          color: 'rgba(0, 0, 0, 0.1)'
        }
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

export default ModelComparisonRadar

