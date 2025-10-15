# 链上数据采集链路已完全移除

## 概述

根据用户要求，链上数据采集链路已被完全移除，不再影响应用的其他功能。系统现在专注于价格数据和新闻情绪数据的处理。

## 移除的内容

### 1. 链上数据采集器 (`custom-scripts/onchain_collector.py`)

**完全重写**：
- 移除了所有数据采集功能
- 移除了模拟数据生成
- 类初始化时直接抛出 `NotImplementedError`
- 提供明确的错误信息指导用户移除相关调用

**新的行为**：
```python
class OnchainCollector(BaseCollector):
    def __init__(self, *args, **kwargs):
        raise NotImplementedError(
            "链上数据采集功能已被禁用。\n"
            "请从以下位置移除相关调用：\n"
            "1. 数据采集脚本\n"
            "2. 工作流配置\n"
            "3. 特征处理器中的链上数据引用"
        )
```

### 2. 数据融合脚本 (`custom-scripts/merge_data.py`)

**已更新**：
- 移除了链上数据合并逻辑
- 仅处理价格数据和新闻数据
- 更新了文档字符串和注释

### 3. 增强版特征处理器 (`custom-scripts/crypto_enhanced_handler.py`)

**已更新**：
- 移除了链上数据特征
- 仅保留价格特征和新闻情绪特征
- 更新了类注释和文档

### 4. 定时调度器 (`custom-scripts/live_trading_scheduler.py`)

**已更新**：
- 移除了链上数据采集任务
- 更新了默认配置
- 链上数据采集方法返回禁用状态

**配置变更**：
```python
# 修改前
"data_collection_schedule": {
    "price_data": "0 */6 * * *",
    "onchain_data": "0 2 * * *",  # 已移除
    "news_data": "0 */2 * * *",
}

# 修改后
"data_collection_schedule": {
    "price_data": "0 */6 * * *",
    "news_data": "0 */2 * * *",
}
```

### 5. 环境变量配置

**已更新**：
- `web-ui/env.example`: 注释掉了 Glassnode API 配置
- `web-ui/docker-compose.yml`: 移除了 Glassnode 环境变量

### 6. 文档更新

**已更新的文档**：
- `README.md`: 更新了数据源描述
- `IMPLEMENTATION_SUMMARY.md`: 修改了链上数据说明
- 创建了 `ONCHAIN_REMOVED.md`: 详细的移除说明文档

## 当前系统状态

### 支持的数据源

1. **价格数据** (Gate.io API)
   - BTC/USDT 和 ETH/USDT 的 K 线数据
   - 支持日线频率
   - 包含 OHLCV 数据

2. **新闻情绪数据** (CryptoPanic API)
   - 新闻标题和内容
   - 情绪分析结果
   - 新闻数量和加权情绪

### 不支持的数据源

1. **链上数据** (已完全移除)
   - ~~链上交易量~~
   - ~~活跃地址数~~
   - ~~交易所净流入~~
   - ~~MVRV 比率~~

## 使用方式

### 1. 数据采集

```bash
# 采集价格数据
python custom-scripts/gate_collector.py

# 采集新闻数据
python custom-scripts/news_collector.py

# 链上数据采集已移除，无需执行
```

### 2. 数据融合

```bash
# 合并价格和新闻数据
python custom-scripts/merge_data.py
```

### 3. 模型训练

```bash
# 使用增强版特征处理器（不包含链上数据）
python -m qlib.run.workflow custom-scripts/crypto_workflow_config.yaml
```

## 错误处理

### 如果尝试使用链上数据采集器

```python
from custom_scripts.onchain_collector import OnchainCollector

# 这会抛出 NotImplementedError
collector = OnchainCollector(save_dir="data/onchain")
```

**错误信息**：
```
NotImplementedError: 链上数据采集功能已被禁用。
请从以下位置移除相关调用：
1. 数据采集脚本
2. 工作流配置
3. 特征处理器中的链上数据引用
```

### 如果尝试运行链上数据采集任务

```python
# 在调度器中手动运行链上数据采集
scheduler.run_job_manually("collect_onchain_data")
```

**返回结果**：
```json
{
    "success": false,
    "error": "On-chain data collection is disabled"
}
```

## 迁移指南

### 从包含链上数据的系统迁移

如果您之前使用了链上数据，请按以下步骤迁移：

1. **移除链上数据采集调用**
   ```python
   # 移除这些调用
   # from custom_scripts.onchain_collector import OnchainCollector
   # collector = OnchainCollector(...)
   ```

2. **更新工作流配置**
   ```yaml
   # 确保配置文件中不包含链上数据相关配置
   # 特征处理器会自动跳过链上数据特征
   ```

3. **更新数据融合脚本**
   ```python
   # 数据融合脚本已自动更新，无需修改
   # 仅处理价格和新闻数据
   ```

4. **验证系统功能**
   ```bash
   # 测试价格数据采集
   python custom-scripts/gate_collector.py

   # 测试新闻数据采集
   python custom-scripts/news_collector.py

   # 测试数据融合
   python custom-scripts/merge_data.py
   ```

## 系统架构变更

### 数据流架构

```
修改前：
外部数据源 → 数据采集器 → 数据标准化 → 数据融合 → Qlib 格式
     │              │              │           │           │
     ▼              ▼              ▼           ▼           ▼
Gate.io API    onchain_collector  normalize  merge_data  .bin 文件
CryptoPanic    news_collector     handler    script      │
Glassnode      gate_collector     │          │           ▼
NewsAPI        │                  ▼          ▼      特征工程
               ▼             标准化数据   融合数据    │
           原始数据              │          │           ▼
                               ▼          ▼      模型训练
                            CSV 文件   Qlib 数据    │
                                                   ▼
                                              模型预测

修改后：
外部数据源 → 数据采集器 → 数据标准化 → 数据融合 → Qlib 格式
     │              │              │           │           │
     ▼              ▼              ▼           ▼           ▼
Gate.io API    gate_collector    normalize  merge_data  .bin 文件
CryptoPanic    news_collector    handler    script      │
NewsAPI        │                  │          │           ▼
               ▼                  ▼          ▼      特征工程
           原始数据           标准化数据   融合数据    │
                               │          │           ▼
                               ▼          ▼      模型训练
                            CSV 文件   Qlib 数据    │
                                                   ▼
                                              模型预测
```

### 特征工程变更

**修改前**：
- 价格特征 (Alpha158)
- 链上数据特征
- 新闻情绪特征

**修改后**：
- 价格特征 (Alpha158)
- 新闻情绪特征

## 性能影响

### 正面影响

1. **简化系统架构**：减少了数据源依赖
2. **降低维护成本**：无需维护链上数据 API
3. **提高系统稳定性**：减少了外部依赖
4. **加快数据处理速度**：减少了数据量

### 潜在影响

1. **特征丰富度降低**：失去了链上数据提供的额外信息
2. **模型性能可能下降**：链上数据可能包含有用的预测信号

## 重新启用链上数据

如果将来需要重新启用链上数据采集，请按以下步骤操作：

### 1. 恢复采集器代码

```python
# 需要重新实现 onchain_collector.py
# 包括 API 调用、数据解析、错误处理等
```

### 2. 配置 API 密钥

```bash
# 在 .env 文件中添加
GLASSNODE_API_KEY=your_glassnode_api_key
# 或
CRYPTOQUANT_API_KEY=your_cryptoquant_api_key
```

### 3. 更新特征处理器

```python
# 在 crypto_enhanced_handler.py 中添加链上数据特征
onchain_features = [
    "$onchain_volume",
    "$active_addresses",
    "$exchange_netflow",
    "$mvrv_ratio",
]
```

### 4. 更新数据融合脚本

```python
# 在 merge_data.py 中添加链上数据合并逻辑
```

### 5. 更新调度器配置

```python
# 在 live_trading_scheduler.py 中恢复链上数据采集任务
```

## 注意事项

1. **向后兼容性**：现有代码无需修改，系统会自动跳过链上数据相关功能
2. **错误处理**：如果代码中仍有链上数据相关调用，会收到明确的错误信息
3. **数据完整性**：系统仍然可以正常运行，只是特征集减少了
4. **模型性能**：可能需要重新训练模型以适应新的特征集

## 总结

链上数据采集链路已被完全移除，系统现在专注于价格数据和新闻情绪数据的处理。这种简化有助于：

- 降低系统复杂度
- 减少外部依赖
- 提高系统稳定性
- 简化维护工作

系统仍然可以正常运行，只是特征集有所减少。如果将来需要链上数据，可以按照上述指南重新启用相关功能。

---

**注意**：链上数据采集功能已被完全移除。如需恢复，请按照重新启用指南操作。
