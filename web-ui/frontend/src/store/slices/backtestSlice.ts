import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface BacktestConfig {
  start_date: string
  end_date: string
  initial_capital: number
  transaction_cost: number
  model_name: string
  strategy_name: string
}

export interface BacktestResult {
  id: string
  config: BacktestConfig
  status: 'running' | 'completed' | 'failed'
  metrics: {
    total_return: number
    annual_return: number
    sharpe_ratio: number
    max_drawdown: number
    win_rate: number
    profit_factor: number
  }
  created_at: string
  completed_at?: string
}

export interface BacktestMetrics {
  returns: number[]
  positions: any[]
  trades: any[]
  equity_curve: { date: string; value: number }[]
}

interface BacktestState {
  results: BacktestResult[]
  currentResult: BacktestResult | null
  metrics: BacktestMetrics | null
  loading: boolean
  error: string | null
  running: boolean
}

const initialState: BacktestState = {
  results: [],
  currentResult: null,
  metrics: null,
  loading: false,
  error: null,
  running: false,
}

// 异步操作
export const fetchBacktests = createAsyncThunk(
  'backtest/fetchBacktests',
  async () => {
    const response = await api.get('/backtest/list')
    return response.data.data
  }
)

export const runBacktest = createAsyncThunk(
  'backtest/runBacktest',
  async (config: BacktestConfig) => {
    const response = await api.post('/backtest/run', config)
    return response.data.data
  }
)

export const fetchBacktestResult = createAsyncThunk(
  'backtest/fetchResult',
  async (resultId: string) => {
    const response = await api.get(`/backtest/results/${resultId}`)
    return response.data.data
  }
)

export const fetchBacktestMetrics = createAsyncThunk(
  'backtest/fetchMetrics',
  async (resultId: string) => {
    const response = await api.get(`/backtest/metrics/${resultId}`)
    return response.data.data
  }
)

export const fetchBacktestChart = createAsyncThunk(
  'backtest/fetchChart',
  async ({ resultId, chartType }: { resultId: string; chartType: string }) => {
    const response = await api.get(`/backtest/chart/${resultId}/${chartType}`)
    return response.data.data
  }
)

export const deleteBacktest = createAsyncThunk(
  'backtest/deleteBacktest',
  async (resultId: string) => {
    const response = await api.delete(`/backtest/results/${resultId}`)
    return response.data.data
  }
)

export const exportBacktest = createAsyncThunk(
  'backtest/exportBacktest',
  async (resultId: string) => {
    const response = await api.post(`/backtest/export/${resultId}`)
    return response.data.data
  }
)

export const compareBacktests = createAsyncThunk(
  'backtest/compareBacktests',
  async (resultIds: string[]) => {
    const response = await api.post('/backtest/compare', { result_ids: resultIds })
    return response.data.data
  }
)

const backtestSlice = createSlice({
  name: 'backtest',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setCurrentResult: (state, action: PayloadAction<BacktestResult>) => {
      state.currentResult = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取回测列表
      .addCase(fetchBacktests.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBacktests.fulfilled, (state, action: PayloadAction<BacktestResult[]>) => {
        state.loading = false
        state.results = action.payload
      })
      .addCase(fetchBacktests.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取回测列表失败'
      })

      // 运行回测
      .addCase(runBacktest.pending, (state) => {
        state.running = true
        state.error = null
      })
      .addCase(runBacktest.fulfilled, (state, action: PayloadAction<BacktestResult>) => {
        state.running = false
        // 检查返回的数据是否有效
        if (action.payload && action.payload.id) {
          state.results.unshift(action.payload)
          state.currentResult = action.payload
        } else {
          state.error = '回测运行失败，请检查配置'
        }
      })
      .addCase(runBacktest.rejected, (state, action) => {
        state.running = false
        state.error = action.error.message || '运行回测失败'
      })

      // 获取回测结果
      .addCase(fetchBacktestResult.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBacktestResult.fulfilled, (state, action: PayloadAction<BacktestResult>) => {
        state.loading = false
        state.currentResult = action.payload
      })
      .addCase(fetchBacktestResult.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取回测结果失败'
      })

      // 获取回测指标
      .addCase(fetchBacktestMetrics.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchBacktestMetrics.fulfilled, (state, action: PayloadAction<BacktestMetrics>) => {
        state.loading = false
        state.metrics = action.payload
      })
      .addCase(fetchBacktestMetrics.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取回测指标失败'
      })

      // 删除回测
      .addCase(deleteBacktest.fulfilled, (state, action) => {
        state.results = state.results.filter(result => result.id !== action.meta.arg)
        if (state.currentResult?.id === action.meta.arg) {
          state.currentResult = null
        }
      })
  },
})

export const { clearError, setCurrentResult } = backtestSlice.actions
export default backtestSlice.reducer
