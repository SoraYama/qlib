# API 使用指南

## 概述

本系统提供 RESTful API 接口，支持数据管理、模型训练、回测分析和实盘交易等功能。

## 基础信息

- **Base URL**: `http://localhost:5000/api`
- **Content-Type**: `application/json`
- **认证方式**: Bearer Token (可选)

## 通用响应格式

### 成功响应

```json
{
  "success": true,
  "data": {...},
  "message": "操作成功"
}
```

### 错误响应

```json
{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}
```

## 数据管理 API

### 获取数据状态

```http
GET /api/data/status
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "price_data": {
      "status": "available",
      "latest_date": "2024-01-15",
      "instruments": ["btcusdt", "ethusdt"],
      "total_records": 1000
    },
    "onchain_data": {
      "status": "available",
      "latest_date": "2024-01-14",
      "metrics": ["transaction_volume", "active_addresses"],
      "total_records": 500
    },
    "news_data": {
      "status": "available",
      "latest_date": "2024-01-15",
      "total_records": 200
    }
  }
}
```

### 更新数据

```http
POST /api/data/update
```

**请求体**:

```json
{
  "data_types": ["price", "onchain", "news"],
  "start_date": "2024-01-01",
  "end_date": "2024-01-15"
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "update_task_123",
    "status": "running",
    "progress": 0
  }
}
```

### 获取数据更新状态

```http
GET /api/data/update/{task_id}
```

## 模型管理 API

### 获取可用模型列表

```http
GET /api/models/list
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "models": [
      {
        "name": "lgb",
        "type": "LightGBM",
        "status": "available",
        "last_trained": "2024-01-15T10:30:00Z",
        "performance": {
          "sharpe_ratio": 1.25,
          "max_drawdown": 0.15,
          "total_return": 0.35
        }
      },
      {
        "name": "xgb",
        "type": "XGBoost",
        "status": "available",
        "last_trained": "2024-01-14T15:20:00Z",
        "performance": {
          "sharpe_ratio": 1.18,
          "max_drawdown": 0.18,
          "total_return": 0.32
        }
      }
    ]
  }
}
```

### 训练模型

```http
POST /api/models/train
```

**请求体**:

```json
{
  "model_name": "lgb",
  "config": {
    "learning_rate": 0.1,
    "max_depth": 8,
    "num_leaves": 127,
    "subsample": 0.8,
    "colsample_bytree": 0.8
  },
  "data_config": {
    "start_date": "2023-01-01",
    "end_date": "2024-01-01",
    "instruments": ["btcusdt", "ethusdt"]
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "task_id": "train_task_456",
    "status": "running",
    "model_name": "lgb",
    "estimated_time": "30 minutes"
  }
}
```

### 获取训练状态

```http
GET /api/models/train/{task_id}
```

### 切换模型

```http
POST /api/models/switch
```

**请求体**:

```json
{
  "model_name": "xgb"
}
```

### 超参数调优

```http
POST /api/models/tune
```

**请求体**:

```json
{
  "model_name": "lgb",
  "param_grid": {
    "learning_rate": [0.01, 0.05, 0.1],
    "max_depth": [6, 8, 10],
    "num_leaves": [31, 63, 127]
  },
  "n_trials": 50
}
```

## 回测分析 API

### 运行回测

```http
POST /api/backtest/run
```

**请求体**:

```json
{
  "model_name": "lgb",
  "config": {
    "start_date": "2023-01-01",
    "end_date": "2023-12-31",
    "initial_capital": 100000,
    "trading_costs": {
      "open_cost": 0.001,
      "close_cost": 0.001,
      "min_cost": 5
    },
    "strategy": {
      "position_size": 0.3,
      "rebalance_frequency": "daily"
    }
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "backtest_id": "backtest_789",
    "status": "running",
    "estimated_time": "5 minutes"
  }
}
```

### 获取回测结果

```http
GET /api/backtest/results/{backtest_id}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "backtest_id": "backtest_789",
    "status": "completed",
    "results": {
      "total_return": 0.35,
      "annual_return": 0.28,
      "sharpe_ratio": 1.25,
      "max_drawdown": 0.15,
      "win_rate": 0.65,
      "total_trades": 120,
      "final_capital": 135000
    },
    "performance_curve": [
      {"date": "2023-01-01", "value": 100000},
      {"date": "2023-01-02", "value": 101200},
      ...
    ],
    "drawdown_curve": [
      {"date": "2023-01-01", "drawdown": 0},
      {"date": "2023-01-02", "drawdown": 0.02},
      ...
    ],
    "positions": [
      {
        "date": "2023-01-01",
        "btcusdt": 0.3,
        "ethusdt": 0.2
      },
      ...
    ]
  }
}
```

### 获取回测历史

```http
GET /api/backtest/history
```

**查询参数**:
- `limit`: 返回数量限制 (默认: 20)
- `offset`: 偏移量 (默认: 0)
- `model_name`: 模型名称过滤

## 实盘交易 API

### 启动交易

```http
POST /api/trading/start
```

**请求体**:

```json
{
  "model_name": "lgb",
  "config": {
    "max_positions": 2,
    "position_size": 0.3,
    "rebalance_frequency": "daily",
    "prediction_threshold": 0.02,
    "min_confidence": 0.6
  }
}
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "trading_id": "trading_101",
    "status": "running",
    "model_name": "lgb",
    "start_time": "2024-01-15T10:30:00Z"
  }
}
```

### 停止交易

```http
POST /api/trading/stop
```

### 获取交易状态

```http
GET /api/trading/status
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "is_running": true,
    "model_name": "lgb",
    "start_time": "2024-01-15T10:30:00Z",
    "last_prediction_time": "2024-01-15T10:30:00Z",
    "last_trade_time": "2024-01-15T10:35:00Z",
    "total_signals": 15,
    "successful_orders": 12,
    "success_rate": 0.8
  }
}
```

### 获取持仓信息

```http
GET /api/trading/positions
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "positions": [
      {
        "symbol": "BTCUSDT",
        "amount": 0.1,
        "entry_price": 45000,
        "current_price": 46000,
        "unrealized_pnl": 100,
        "unrealized_pnl_ratio": 0.022
      },
      {
        "symbol": "ETHUSDT",
        "amount": 1.0,
        "entry_price": 3000,
        "current_price": 3100,
        "unrealized_pnl": 100,
        "unrealized_pnl_ratio": 0.033
      }
    ],
    "total_value": 50000,
    "total_pnl": 200,
    "total_pnl_ratio": 0.004
  }
}
```

### 获取订单历史

```http
GET /api/trading/orders
```

**查询参数**:
- `limit`: 返回数量限制 (默认: 50)
- `offset`: 偏移量 (默认: 0)
- `status`: 订单状态过滤
- `symbol`: 交易对过滤

**响应示例**:

```json
{
  "success": true,
  "data": {
    "orders": [
      {
        "order_id": "order_123",
        "symbol": "BTCUSDT",
        "side": "buy",
        "amount": 0.1,
        "price": 45000,
        "total": 4500,
        "fee": 4.5,
        "status": "completed",
        "created_at": "2024-01-15T10:35:00Z",
        "updated_at": "2024-01-15T10:35:05Z"
      }
    ],
    "total": 100,
    "has_more": true
  }
}
```

### 获取账户信息

```http
GET /api/trading/account
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "currencies": [
      {
        "currency": "USDT",
        "available": 25000,
        "locked": 0,
        "total": 25000
      },
      {
        "currency": "BTC",
        "available": 0.1,
        "locked": 0,
        "total": 0.1
      }
    ],
    "total_balance": 50000,
    "trading_enabled": true,
    "last_update": "2024-01-15T10:30:00Z"
  }
}
```

## 风险管理 API

### 获取风险指标

```http
GET /api/risk/metrics
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "total_portfolio_value": 50000,
    "total_exposure": 0.6,
    "max_drawdown": 0.12,
    "current_drawdown": 0.05,
    "daily_pnl": 500,
    "weekly_pnl": 2000,
    "sharpe_ratio": 1.25,
    "var_95": 0.02,
    "cvar_95": 0.03,
    "concentration_risk": 0.4,
    "correlation_risk": 0.2
  }
}
```

### 获取风险告警

```http
GET /api/risk/alerts
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "alerts": [
      {
        "id": "alert_123",
        "type": "drawdown",
        "severity": "high",
        "message": "当前回撤 15% 接近限制 20%",
        "created_at": "2024-01-15T10:30:00Z",
        "is_read": false
      }
    ],
    "unread_count": 1
  }
```

### 更新风险配置

```http
POST /api/risk/config
```

**请求体**:

```json
{
  "max_position_size": 0.25,
  "max_drawdown": 0.15,
  "stop_loss": 0.03,
  "max_daily_loss": 0.03
}
```

## 系统监控 API

### 获取系统状态

```http
GET /api/system/status
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "services": {
      "backend": "running",
      "frontend": "running",
      "database": "running",
      "redis": "running"
    },
    "system_info": {
      "cpu_usage": 45.2,
      "memory_usage": 68.5,
      "disk_usage": 32.1,
      "uptime": "2 days, 5 hours"
    },
    "last_update": "2024-01-15T10:30:00Z"
  }
}
```

### 获取调度任务状态

```http
GET /api/system/scheduler
```

**响应示例**:

```json
{
  "success": true,
  "data": {
    "is_running": true,
    "jobs": [
      {
        "id": "collect_price_data",
        "name": "Collect Price Data",
        "schedule": "0 */6 * * *",
        "last_run": "2024-01-15T06:00:00Z",
        "status": "completed"
      },
      {
        "id": "daily_trading",
        "name": "Daily Trading",
        "schedule": "0 9 * * 1-5",
        "last_run": "2024-01-15T09:00:00Z",
        "status": "completed"
      }
    ]
  }
}
```

## 错误代码

| 代码 | 描述 |
|------|------|
| `INVALID_PARAMETER` | 参数无效 |
| `MODEL_NOT_FOUND` | 模型不存在 |
| `DATA_NOT_AVAILABLE` | 数据不可用 |
| `TRADING_DISABLED` | 交易已禁用 |
| `INSUFFICIENT_BALANCE` | 余额不足 |
| `ORDER_FAILED` | 订单失败 |
| `RISK_LIMIT_EXCEEDED` | 超出风险限制 |
| `SYSTEM_ERROR` | 系统错误 |

## 使用示例

### Python 客户端示例

```python
import requests

# 基础配置
BASE_URL = "http://localhost:5000/api"
headers = {"Content-Type": "application/json"}

# 获取数据状态
response = requests.get(f"{BASE_URL}/data/status")
data_status = response.json()

# 训练模型
train_data = {
    "model_name": "lgb",
    "config": {
        "learning_rate": 0.1,
        "max_depth": 8
    }
}
response = requests.post(f"{BASE_URL}/models/train", json=train_data)
train_result = response.json()

# 运行回测
backtest_data = {
    "model_name": "lgb",
    "config": {
        "start_date": "2023-01-01",
        "end_date": "2023-12-31",
        "initial_capital": 100000
    }
}
response = requests.post(f"{BASE_URL}/backtest/run", json=backtest_data)
backtest_result = response.json()
```

### JavaScript 客户端示例

```javascript
// 基础配置
const BASE_URL = 'http://localhost:5000/api';

// 获取数据状态
async function getDataStatus() {
    const response = await fetch(`${BASE_URL}/data/status`);
    const data = await response.json();
    return data;
}

// 训练模型
async function trainModel(modelName, config) {
    const response = await fetch(`${BASE_URL}/models/train`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model_name: modelName,
            config: config
        })
    });
    const data = await response.json();
    return data;
}

// 运行回测
async function runBacktest(modelName, config) {
    const response = await fetch(`${BASE_URL}/backtest/run`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            model_name: modelName,
            config: config
        })
    });
    const data = await response.json();
    return data;
}
```

## 注意事项

1. **API 限制**: 默认请求频率限制为 10 次/秒
2. **数据格式**: 所有日期格式为 ISO 8601 (YYYY-MM-DD)
3. **异步操作**: 训练和回测等操作是异步的，需要通过任务 ID 查询状态
4. **错误处理**: 请妥善处理 API 错误响应
5. **安全性**: 生产环境请使用 HTTPS 和适当的认证机制

