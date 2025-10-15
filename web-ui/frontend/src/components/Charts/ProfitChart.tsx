import React, { useEffect, useState } from 'react'
import ReactECharts from 'echarts-for-react'
import { Spin } from 'antd'

interface ProfitChartProps {
  height?: number
}

const ProfitChart: React.FC<ProfitChartProps> = ({ height = 400 }) => {
  const [loading, setLoading] = useState(true)
  const [chartData, setChartData] = useState<{ date: string; value: number }[]>([])

  useEffect(() => {
    // 模拟数据加载
    const loadChartData = async () => {
      setLoading(true)

      // 模拟API调用
      setTimeout(() => {
        // 生成模拟数据
        const data = []
        const startDate = new Date('2024-01-01')
        let value = 100000

        for (let i = 0; i < 100; i++) {
          const date = new Date(startDate)
          date.setDate(date.getDate() + i)

          // 模拟价格波动
          const change = (Math.random() - 0.5) * 0.05
          value = value * (1 + change)

          data.push({
            date: date.toISOString().split('T')[0],
            value: Math.round(value)
          })
        }

        setChartData(data)
        setLoading(false)
      }, 1000)
    }

    loadChartData()
  }, [])

  const option = {
    title: {
      text: '资产价值变化',
      left: 'center',
      textStyle: {
        fontSize: 16,
        fontWeight: 'normal'
      }
    },
    tooltip: {
      trigger: 'axis',
      formatter: (params: any) => {
        const data = params[0]
        return `
          <div>
            <div>日期: ${data.axisValue}</div>
            <div>资产: ¥${data.value.toLocaleString()}</div>
          </div>
        `
      }
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: chartData.map(item => item.date),
      axisLabel: {
        formatter: (value: string) => {
          const date = new Date(value)
          return `${date.getMonth() + 1}/${date.getDate()}`
        }
      }
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => `¥${(value / 1000).toFixed(0)}k`
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
        data: chartData.map(item => item.value)
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

  return (
    <ReactECharts
      option={option}
      style={{ height }}
      opts={{ renderer: 'canvas' }}
    />
  )
}

export default ProfitChart
