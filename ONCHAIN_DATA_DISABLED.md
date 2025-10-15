# 链上数据采集已禁用

## 概述

根据用户要求，链上数据采集功能已被禁用。系统现在仅使用模拟数据来替代真实的链上数据，以便在没有 API 密钥的情况下继续开发和测试。

## 修改内容

### 1. 链上数据采集器 (`custom-scripts/onchain_collector.py`)

**主要修改**：
- 移除了所有外部 API 调用（Glassnode、CryptoQuant）
- 仅保留模拟数据生成功能
- 更新了类注释和文档字符串
- 简化了数据获取流程

**具体变更**：
```python
# 修改前
class OnchainCollector(BaseCollector):
    """链上数据采集器，仅支持 Glassnode API（CryptoQuant 已禁用）"""

    GLASSNODE_METRICS = {
        "BTCUSDT": {
            "transaction_volume": "transactions/count",
            # ...
        }
    }

# 修改后
class OnchainCollector(BaseCollector):
    """链上数据采集器（已禁用 - 无 API 密钥）"""

    MOCK_METRICS = {
        "BTCUSDT": {
            "transaction_volume": "mock_transaction_volume",
            # ...
        }
    }
```

**API 方法更新**：
- 移除了 `_fetch_glassnode_data()` 方法
- 添加了 `_fetch_mock_data()` 方法
- 简化了 `get_data()` 方法，直接返回模拟数据

### 2. 环境变量配置

**修改文件**：
- `web-ui/env.example`
- `web-ui/docker-compose.yml`

**移除的配置**：
```bash
# 已注释掉
# GLASSNODE_API_KEY=your_glassnode_api_key
```

### 3. 文档更新

**更新的文档**：
- `README.md`
- `IMPLEMENTATION_SUMMARY.md`

**主要变更**：
- 更新了数据源描述
- 标记了链上数据为已禁用状态
- 说明了使用模拟数据的情况

## 当前状态

### 模拟数据生成

系统现在会自动生成以下链上指标的模拟数据：

1. **链上交易量** (`transaction_volume`)
   - BTC: 基础值 300,000 + 10% 随机波动
   - ETH: 基础值 1,000,000 + 10% 随机波动

2. **活跃地址数** (`active_addresses`)
   - BTC: 基础值 800,000 + 5% 随机波动
   - ETH: 基础值 500,000 + 5% 随机波动

3. **交易所净流入** (`exchange_netflow`)
   - 正负随机波动，标准差 1000

4. **MVRV 比率** (`mvrv_ratio`)
   - 1.0 附近波动，标准差 0.2

### 数据格式

模拟数据仍然保持与真实数据相同的格式：

```python
# 返回的数据框包含以下列：
{
    'date': '2024-01-01',
    'transaction_volume': 320000.0,
    'active_addresses': 850000.0,
    'exchange_netflow': 150.0,
    'mvrv_ratio': 1.15
}
```

## 使用方式

### 1. 初始化采集器

```python
from custom_scripts.onchain_collector import OnchainCollector

collector = OnchainCollector(
    save_dir="data/onchain",
    start="2024-01-01",
    end="2024-01-15"
)
```

### 2. 获取模拟数据

```python
# 获取 BTC 链上数据（模拟）
btc_data = collector.get_data(
    symbol="BTCUSDT",
    interval="1d",
    start_datetime=pd.Timestamp("2024-01-01"),
    end_datetime=pd.Timestamp("2024-01-15")
)

print(btc_data.head())
```

### 3. 日志输出

系统会输出以下日志信息：
```
WARNING: 链上数据采集已禁用 - 无 API 密钥配置
INFO: 将使用模拟数据进行开发和测试
INFO: 链上数据采集已禁用，为 BTCUSDT 生成模拟数据
INFO: Successfully generated 15 mock records for BTCUSDT
```

## 数据质量说明

### 模拟数据特点

1. **真实性**：基于真实数据的统计特征生成
2. **随机性**：包含合理的随机波动
3. **一致性**：不同指标之间的相关性
4. **完整性**：无缺失值，数据连续

### 使用建议

1. **开发测试**：模拟数据完全适用于开发和测试
2. **特征工程**：可以正常进行特征工程和模型训练
3. **回测分析**：回测结果仅供参考，不代表真实市场表现
4. **实盘交易**：不建议直接用于实盘交易决策

## 重新启用链上数据

如果将来需要重新启用链上数据采集，请按以下步骤操作：

### 1. 获取 API 密钥

选择以下任一数据源：
- **Glassnode**: https://glassnode.com/
- **CryptoQuant**: https://cryptoquant.com/

### 2. 配置环境变量

```bash
# 在 .env 文件中添加
GLASSNODE_API_KEY=your_glassnode_api_key
# 或
CRYPTOQUANT_API_KEY=your_cryptoquant_api_key
```

### 3. 修改代码

恢复 `onchain_collector.py` 中的 API 调用逻辑：
- 取消注释 API 相关代码
- 恢复真实数据获取方法
- 更新配置映射

### 4. 测试验证

```bash
# 测试链上数据采集
python custom-scripts/onchain_collector.py
```

## 注意事项

1. **数据延迟**：真实链上数据通常有 1-2 天延迟
2. **API 限制**：注意各数据源的请求频率限制
3. **数据质量**：定期检查数据完整性和准确性
4. **成本考虑**：部分数据源需要付费订阅

## 故障排除

### 常见问题

1. **模拟数据异常**
   ```
   Error: Error generating mock onchain data
   ```
   **解决方案**：检查日期范围是否正确

2. **数据格式错误**
   ```
   Error: Invalid data format
   ```
   **解决方案**：确保使用正确的数据列名

3. **内存不足**
   ```
   Error: Memory error
   ```
   **解决方案**：减少数据时间范围或分批处理

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 未来计划

1. **数据源扩展**：考虑集成其他免费数据源
2. **数据缓存**：实现本地数据缓存机制
3. **数据验证**：添加数据质量检查
4. **实时更新**：支持实时数据流

---

**注意**：链上数据采集已被禁用。如需恢复，请配置相应的 API 密钥并修改代码。
