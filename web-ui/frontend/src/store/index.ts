import { configureStore } from '@reduxjs/toolkit'
import dataReducer from './slices/dataSlice'
import modelReducer from './slices/modelSlice'
import backtestReducer from './slices/backtestSlice'
import tradingReducer from './slices/tradingSlice'
import dashboardReducer from './slices/dashboardSlice'

export const store = configureStore({
  reducer: {
    data: dataReducer,
    model: modelReducer,
    backtest: backtestReducer,
    trading: tradingReducer,
    dashboard: dashboardReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
