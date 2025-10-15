import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '../../services/api'

export interface ModelInfo {
  name: string
  class: string
  description: string
  tunable_params: string[]
  default_params: Record<string, any>
}

export interface ModelPerformance {
  accuracy: number
  precision: number
  recall: number
  f1_score: number
  sharpe_ratio: number
  max_drawdown: number
  annual_return: number
}

interface ModelState {
  models: ModelInfo[]
  currentModel: string | null
  performance: ModelPerformance | null
  loading: boolean
  error: string | null
  training: boolean
  predicting: boolean
}

const initialState: ModelState = {
  models: [],
  currentModel: null,
  performance: null,
  loading: false,
  error: null,
  training: false,
  predicting: false,
}

// 异步操作
export const fetchModels = createAsyncThunk(
  'model/fetchModels',
  async () => {
    const response = await api.get('/model/list')
    return response.data.data
  }
)

export const fetchModelInfo = createAsyncThunk(
  'model/fetchModelInfo',
  async (modelName: string) => {
    const response = await api.get(`/model/info/${modelName}`)
    return response.data.data
  }
)

export const switchModel = createAsyncThunk(
  'model/switchModel',
  async (modelName: string) => {
    const response = await api.post('/model/switch', { model_name: modelName })
    return response.data.data
  }
)

export const updateModelParams = createAsyncThunk(
  'model/updateParams',
  async ({ modelName, params }: { modelName: string; params: Record<string, any> }) => {
    const response = await api.post(`/model/params/${modelName}`, { params })
    return response.data.data
  }
)

export const trainModel = createAsyncThunk(
  'model/trainModel',
  async ({ modelName, params }: { modelName: string; params?: Record<string, any> }) => {
    const response = await api.post('/model/train', {
      model_name: modelName,
      params: params || {}
    })
    return response.data.data
  }
)

export const tuneHyperparameters = createAsyncThunk(
  'model/tuneHyperparameters',
  async ({ modelName, nTrials, timeout }: {
    modelName: string;
    nTrials?: number;
    timeout?: number
  }) => {
    const response = await api.post(`/model/tune/${modelName}`, {
      n_trials: nTrials || 100,
      timeout: timeout || 3600
    })
    return response.data.data
  }
)

export const predict = createAsyncThunk(
  'model/predict',
  async ({ modelName, data }: { modelName: string; data: any }) => {
    const response = await api.post('/model/predict', {
      model_name: modelName,
      data
    })
    return response.data.data
  }
)

export const fetchModelPerformance = createAsyncThunk(
  'model/fetchPerformance',
  async (modelName: string) => {
    const response = await api.get(`/model/performance/${modelName}`)
    return response.data.data
  }
)

export const compareModels = createAsyncThunk(
  'model/compareModels',
  async (models?: string[]) => {
    const response = await api.post('/model/compare', { models: models || [] })
    return response.data.data
  }
)

const modelSlice = createSlice({
  name: 'model',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    setCurrentModel: (state, action: PayloadAction<string>) => {
      state.currentModel = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      // 获取模型列表
      .addCase(fetchModels.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchModels.fulfilled, (state, action: PayloadAction<ModelInfo[]>) => {
        state.loading = false
        state.models = action.payload
      })
      .addCase(fetchModels.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取模型列表失败'
      })

      // 切换模型
      .addCase(switchModel.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(switchModel.fulfilled, (state, action) => {
        state.loading = false
        state.currentModel = action.payload.name
      })
      .addCase(switchModel.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '切换模型失败'
      })

      // 训练模型
      .addCase(trainModel.pending, (state) => {
        state.training = true
        state.error = null
      })
      .addCase(trainModel.fulfilled, (state) => {
        state.training = false
      })
      .addCase(trainModel.rejected, (state, action) => {
        state.training = false
        state.error = action.error.message || '训练模型失败'
      })

      // 超参数调优
      .addCase(tuneHyperparameters.pending, (state) => {
        state.training = true
        state.error = null
      })
      .addCase(tuneHyperparameters.fulfilled, (state) => {
        state.training = false
      })
      .addCase(tuneHyperparameters.rejected, (state, action) => {
        state.training = false
        state.error = action.error.message || '超参数调优失败'
      })

      // 模型预测
      .addCase(predict.pending, (state) => {
        state.predicting = true
        state.error = null
      })
      .addCase(predict.fulfilled, (state) => {
        state.predicting = false
      })
      .addCase(predict.rejected, (state, action) => {
        state.predicting = false
        state.error = action.error.message || '模型预测失败'
      })

      // 获取模型性能
      .addCase(fetchModelPerformance.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchModelPerformance.fulfilled, (state, action: PayloadAction<ModelPerformance>) => {
        state.loading = false
        state.performance = action.payload
      })
      .addCase(fetchModelPerformance.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取模型性能失败'
      })
  },
})

export const { clearError, setCurrentModel } = modelSlice.actions
export default modelSlice.reducer
