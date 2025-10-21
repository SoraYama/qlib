import React from 'react'
import ReactECharts from 'echarts-for-react'

interface KlinePoint {
  time: number
  open: number
  high: number
  low: number
  close: number
  volume: number
}

interface TradingPlan {
  symbol?: string
  plan_time?: string
  signal?: 'buy' | 'sell' | 'wait'
  entry?: number | null
  stop?: number | null
  take?: number | null
}

interface KlineChartProps {
  data: KlinePoint[]
  plan?: TradingPlan | null
  height?: number
  title?: string
}

const KlineChart: React.FC<KlineChartProps> = ({ data, plan, height = 420, title = '实时K线' }) => {
  const categories = data.map(d => new Date(d.time * 1000).toLocaleTimeString())
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = data.map(d => d.volume)

  const markLines: any[] = []
  if (plan && plan.entry) {
    markLines.push({
      yAxis: plan.entry,
      name: `Entry ${plan.entry.toFixed(2)}`,
      lineStyle: { color: '#1890ff' },
      label: { formatter: 'Entry' }
    })
  }
  if (plan && plan.stop) {
    markLines.push({
      yAxis: plan.stop,
      name: `Stop ${plan.stop.toFixed(2)}`,
      lineStyle: { color: '#ff4d4f' },
      label: { formatter: 'Stop' }
    })
  }
  if (plan && plan.take) {
    markLines.push({
      yAxis: plan.take,
      name: `Take ${plan.take.toFixed(2)}`,
      lineStyle: { color: '#52c41a' },
      label: { formatter: 'Take' }
    })
  }

  const option = {
    title: { text: title, left: 'center' },
    tooltip: { trigger: 'axis' },
    axisPointer: { link: [{ xAxisIndex: 'all' }] },
    grid: [
      { left: '3%', right: '3%', height: '65%' },
      { left: '3%', right: '3%', top: '76%', height: '18%' }
    ],
    xAxis: [
      { type: 'category', data: categories, boundaryGap: true, axisLine: { onZero: false } },
      { type: 'category', data: categories, gridIndex: 1, boundaryGap: true, axisLine: { onZero: false } }
    ],
    yAxis: [
      { scale: true },
      { scale: true, gridIndex: 1 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1] },
      { type: 'slider', xAxisIndex: [0, 1] }
    ],
    series: [
      {
        name: 'Kline',
        type: 'candlestick',
        data: ohlc,
        itemStyle: { color: '#ec0000', color0: '#00aa3b', borderColor: '#8A0000', borderColor0: '#008F28' },
        markLine: markLines.length > 0 ? { symbol: 'none', data: markLines } : undefined
      },
      {
        name: 'Volume',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: { color: '#999' }
      }
    ]
  }

  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ color: '#999' }}>暂无K线数据</div>
      </div>
    )
  }

  return (
    <ReactECharts option={option} style={{ height }} opts={{ renderer: 'canvas' }} />
  )
}

export default KlineChart


