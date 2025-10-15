import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface DataStatus {
  qlib_data_dir: string
  data_exists: boolean
  instruments: string[]
  date_range: {
    start: string
    end: string
    total_days: number
  }
  features: string[]
}

export interface DataQuality {
  missing_data: Record<string, any>
  outliers: Record<string, any>
  data_consistency: Record<string, any>
  overall_score: number
}

interface DataState {
  status: DataStatus | null
  quality: DataQuality | null
  instruments: string[]
  features: string[]
  loading: boolean
  error: string | null
  updating: boolean
}

const initialState: DataState = {
  status: null,
  quality: null,
  instruments: [],
  features: [],
  loading: false,
  error: null,
  updating: false,
}

// 异步操作
export const fetchDataStatus = createAsyncThunk(
  'data/fetchStatus',
  async () => {
    const response = await api.get('/data/status')
    return response.data.data
  }
)

export const fetchDataQuality = createAsyncThunk(
  'data/fetchQuality',
  async () => {
    const response = await api.get('/data/quality')
    return response.data.data
  }
)

export const fetchInstruments = createAsyncThunk(
  'data/fetchInstruments',
  async () => {
    const response = await api.get('/data/instruments')
    return response.data.data
  }
)

export const fetchFeatures = createAsyncThunk(
  'data/fetchFeatures',
  async () => {
    const response = await api.get('/data/features')
    return response.data.data
  }
)

export const updateData = createAsyncThunk(
  'data/updateData',
  async (dataType: string) => {
    const response = await api.post('/data/update', { type: dataType })
    return response.data.data
  }
)

export const mergeData = createAsyncThunk(
  'data/mergeData',
  async () => {
    const response = await api.post('/data/merge')
    return response.data.data
  }
)

const dataSlice = createSlice({
  name: 'data',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取数据状态
      .addCase(fetchDataStatus.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchDataStatus.fulfilled, (state, action: PayloadAction<DataStatus>) => {
        state.loading = false
        state.status = action.payload
      })
      .addCase(fetchDataStatus.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取数据状态失败'
      })

      // 获取数据质量
      .addCase(fetchDataQuality.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchDataQuality.fulfilled, (state, action: PayloadAction<DataQuality>) => {
        state.loading = false
        state.quality = action.payload
      })
      .addCase(fetchDataQuality.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取数据质量失败'
      })

      // 获取交易对
      .addCase(fetchInstruments.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchInstruments.fulfilled, (state, action: PayloadAction<string[]>) => {
        state.loading = false
        state.instruments = action.payload
      })
      .addCase(fetchInstruments.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取交易对失败'
      })

      // 获取特征
      .addCase(fetchFeatures.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchFeatures.fulfilled, (state, action: PayloadAction<string[]>) => {
        state.loading = false
        state.features = action.payload
      })
      .addCase(fetchFeatures.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取特征失败'
      })

      // 更新数据
      .addCase(updateData.pending, (state) => {
        state.updating = true
        state.error = null
      })
      .addCase(updateData.fulfilled, (state) => {
        state.updating = false
      })
      .addCase(updateData.rejected, (state, action) => {
        state.updating = false
        state.error = action.error.message || '更新数据失败'
      })

      // 合并数据
      .addCase(mergeData.pending, (state) => {
        state.updating = true
        state.error = null
      })
      .addCase(mergeData.fulfilled, (state) => {
        state.updating = false
      })
      .addCase(mergeData.rejected, (state, action) => {
        state.updating = false
        state.error = action.error.message || '合并数据失败'
      })
  },
})

export const { clearError } = dataSlice.actions
export default dataSlice.reducer
