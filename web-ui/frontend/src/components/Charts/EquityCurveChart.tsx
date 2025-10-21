import React from 'react'
import ReactECharts from 'echarts-for-react'
import { Spin } from 'antd'

interface EquityCurveChartProps {
  data: { date: string; value: number }[]
  loading?: boolean
  height?: number
  title?: string
}

const EquityCurveChart: React.FC<EquityCurveChartProps> = ({
  data,
  loading = false,
  height = 400,
  title = '收益曲线'
}) => {
  const option = {
    title: {
      text: title,
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const dataPoint = params[0]
        return `
          <div>
            <div><strong>日期:</strong> ${dataPoint.axisValue}</div>
            <div><strong>资产:</strong> ¥${dataPoint.value.toLocaleString()}</div>
          </div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '15%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: data.map(item => item.date),
      axisLabel: {
        formatter: (value: string) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        },
        rotate: 45
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => {
          if (value >= 1000000) {
            return `¥${(value / 1000000).toFixed(1)}M`
          } else if (value >= 1000) {
            return `¥${(value / 1000).toFixed(0)}k`
          }
          return `¥${value}`
        }
      }
    },
    series: [
      {
        name: '资产价值',
        type: 'line',
        smooth: true,
        lineStyle: {
          color: '#1890ff',
          width: 2
        },
        areaStyle: {
          color: {
            type: 'linear',
            x: 0,
            y: 0,
            x2: 0,
            y2: 1,
            colorStops: [
              {
                offset: 0,
                color: 'rgba(24, 144, 255, 0.3)'
              },
              {
                offset: 1,
                color: 'rgba(24, 144, 255, 0.05)'
              }
            ]
          }
        },
        data: data.map(item => item.value)
      }
    ]
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

export default EquityCurveChart

