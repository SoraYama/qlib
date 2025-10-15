import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface Position {
  symbol: string
  side: 'long' | 'short'
  size: number
  entry_price: number
  current_price: number
  unrealized_pnl: number
  realized_pnl: number
  timestamp: string
}

export interface Order {
  id: string
  symbol: string
  side: 'buy' | 'sell'
  type: 'market' | 'limit'
  amount: number
  price?: number
  status: 'pending' | 'filled' | 'cancelled' | 'rejected'
  created_at: string
  filled_at?: string
}

export interface TradingStatus {
  is_running: boolean
  current_strategy: string
  risk_limits: {
    max_position_size: number
    max_drawdown: number
    stop_loss: number
  }
  account_info: {
    total_balance: number
    available_balance: number
    total_pnl: number
    daily_pnl: number
  }
}

interface TradingState {
  status: TradingStatus | null
  positions: Position[]
  orders: Order[]
  loading: boolean
  error: string | null
  starting: boolean
  stopping: boolean
}

const initialState: TradingState = {
  status: null,
  positions: [],
  orders: [],
  loading: false,
  error: null,
  starting: false,
  stopping: false,
}

// 异步操作
export const fetchTradingStatus = createAsyncThunk(
  'trading/fetchStatus',
  async () => {
    const response = await api.get('/trading/status')
    return response.data.data
  }
)

export const startTrading = createAsyncThunk(
  'trading/startTrading',
  async (config: { strategy_name: string; risk_limits: any }) => {
    const response = await api.post('/trading/start', config)
    return response.data.data
  }
)

export const stopTrading = createAsyncThunk(
  'trading/stopTrading',
  async () => {
    const response = await api.post('/trading/stop')
    return response.data.data
  }
)

export const fetchPositions = createAsyncThunk(
  'trading/fetchPositions',
  async () => {
    const response = await api.get('/trading/positions')
    return response.data.data
  }
)

export const fetchOrders = createAsyncThunk(
  'trading/fetchOrders',
  async () => {
    const response = await api.get('/trading/orders')
    return response.data.data
  }
)

export const updateRiskLimits = createAsyncThunk(
  'trading/updateRiskLimits',
  async (limits: { max_position_size?: number; max_drawdown?: number; stop_loss?: number }) => {
    const response = await api.post('/trading/risk-limits', limits)
    return response.data.data
  }
)

export const closePosition = createAsyncThunk(
  'trading/closePosition',
  async (symbol: string) => {
    const response = await api.post(`/trading/close-position/${symbol}`)
    return response.data.data
  }
)

export const cancelOrder = createAsyncThunk(
  'trading/cancelOrder',
  async (orderId: string) => {
    const response = await api.post(`/trading/cancel-order/${orderId}`)
    return response.data.data
  }
)

const tradingSlice = createSlice({
  name: 'trading',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取交易状态
      .addCase(fetchTradingStatus.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchTradingStatus.fulfilled, (state, action: PayloadAction<TradingStatus>) => {
        state.loading = false
        state.status = action.payload
      })
      .addCase(fetchTradingStatus.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取交易状态失败'
      })

      // 启动交易
      .addCase(startTrading.pending, (state) => {
        state.starting = true
        state.error = null
      })
      .addCase(startTrading.fulfilled, (state, action) => {
        state.starting = false
        if (state.status) {
          state.status.is_running = true
          state.status.current_strategy = action.payload.strategy_name
        }
      })
      .addCase(startTrading.rejected, (state, action) => {
        state.starting = false
        state.error = action.error.message || '启动交易失败'
      })

      // 停止交易
      .addCase(stopTrading.pending, (state) => {
        state.stopping = true
        state.error = null
      })
      .addCase(stopTrading.fulfilled, (state) => {
        state.stopping = false
        if (state.status) {
          state.status.is_running = false
        }
      })
      .addCase(stopTrading.rejected, (state, action) => {
        state.stopping = false
        state.error = action.error.message || '停止交易失败'
      })

      // 获取持仓
      .addCase(fetchPositions.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchPositions.fulfilled, (state, action: PayloadAction<Position[]>) => {
        state.loading = false
        state.positions = action.payload
      })
      .addCase(fetchPositions.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取持仓失败'
      })

      // 获取订单
      .addCase(fetchOrders.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchOrders.fulfilled, (state, action: PayloadAction<Order[]>) => {
        state.loading = false
        state.orders = action.payload
      })
      .addCase(fetchOrders.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取订单失败'
      })

      // 更新风险限制
      .addCase(updateRiskLimits.fulfilled, (state, action) => {
        if (state.status) {
          state.status.risk_limits = { ...state.status.risk_limits, ...action.payload }
        }
      })
  },
})

export const { clearError } = tradingSlice.actions
export default tradingSlice.reducer
