import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface DashboardAccount {
  total_balance: number
  available_balance: number
  total_pnl: number
  daily_pnl: number
}

export interface DashboardPositions {
  active_count: number
  total_value: number
}

export interface DashboardSystem {
  services: {
    backend: string
    database: string
    redis: string
    trading_system: string
  }
  data_status: {
    instruments_count: number
    features_count: number
    date_range_days: number
  }
}

export interface DashboardSummary {
  account: DashboardAccount
  positions: DashboardPositions
  system: DashboardSystem
  last_update: string
}

interface DashboardState {
  summary: DashboardSummary | null
  loading: boolean
  error: string | null
}

const initialState: DashboardState = {
  summary: null,
  loading: false,
  error: null,
}

// 异步操作
export const fetchDashboardSummary = createAsyncThunk(
  'dashboard/fetchSummary',
  async () => {
    const response = await api.get('/dashboard/summary')
    return response.data.data
  }
)

export const fetchSystemHealth = createAsyncThunk(
  'dashboard/fetchHealth',
  async () => {
    const response = await api.get('/dashboard/health')
    return response.data.data
  }
)

const dashboardSlice = createSlice({
  name: 'dashboard',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取仪表盘汇总数据
      .addCase(fetchDashboardSummary.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchDashboardSummary.fulfilled, (state, action: PayloadAction<DashboardSummary>) => {
        state.loading = false
        state.summary = action.payload
      })
      .addCase(fetchDashboardSummary.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取仪表盘数据失败'
      })

      // 获取系统健康状态
      .addCase(fetchSystemHealth.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchSystemHealth.fulfilled, (state) => {
        state.loading = false
      })
      .addCase(fetchSystemHealth.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取系统健康状态失败'
      })
  },
})

export const { clearError } = dashboardSlice.actions
export default dashboardSlice.reducer
