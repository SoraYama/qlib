import React from 'react'
import { Table, Tag, Button, Space, Typography } from 'antd'
import { useSelector } from 'react-redux'
import { RootState } from '../../store'
import { Position } from '../../store/slices/tradingSlice'

const { Text } = Typography

const PositionTable: React.FC = () => {
  const { positions, loading } = useSelector((state: RootState) => state.trading)

  const columns = [
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
        <Tag color={side === 'long' ? 'green' : 'red'}>
          {side === 'long' ? '多头' : '空头'}
        </Tag>
      ),
    },
    {
      title: '数量',
      dataIndex: 'size',
      key: 'size',
      render: (size: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          {size.toFixed(6)}
        </Text>
      ),
    },
    {
      title: '入场价格',
      dataIndex: 'entry_price',
      key: 'entry_price',
      render: (price: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          ${price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '当前价格',
      dataIndex: 'current_price',
      key: 'current_price',
      render: (price: number) => (
        <Text style={{ fontFamily: 'monospace' }}>
          ${price.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '未实现盈亏',
      dataIndex: 'unrealized_pnl',
      key: 'unrealized_pnl',
      render: (pnl: number) => (
        <Text
          style={{
            fontFamily: 'monospace',
            color: pnl >= 0 ? '#52c41a' : '#ff4d4f'
          }}
        >
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '已实现盈亏',
      dataIndex: 'realized_pnl',
      key: 'realized_pnl',
      render: (pnl: number) => (
        <Text
          style={{
            fontFamily: 'monospace',
            color: pnl >= 0 ? '#52c41a' : '#ff4d4f'
          }}
        >
          {pnl >= 0 ? '+' : ''}${pnl.toFixed(2)}
        </Text>
      ),
    },
    {
      title: '操作',
      key: 'action',
      render: (_: any, record: Position) => (
        <Space size="small">
          <Button
            type="link"
            size="small"
            onClick={() => handleClosePosition(record.symbol)}
          >
            平仓
          </Button>
        </Space>
      ),
    },
  ]

  const handleClosePosition = (symbol: string) => {
    // 这里应该调用平仓API
    console.log('平仓:', symbol)
  }

  return (
    <Table
      columns={columns}
      dataSource={positions}
      loading={loading}
      rowKey="symbol"
      pagination={{
        pageSize: 10,
        showSizeChanger: true,
        showQuickJumper: true,
        showTotal: (total, range) =>
          `第 ${range[0]}-${range[1]} 条/共 ${total} 条`,
      }}
      locale={{
        emptyText: '暂无持仓数据'
      }}
    />
  )
}

export default PositionTable
