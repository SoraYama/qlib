# CryptoQuant 集成已禁用

## 概述

根据用户要求，CryptoQuant API 的获取和分析功能已被屏蔽。系统现在仅支持 Glassnode API 作为链上数据源。

## 修改内容

### 1. 链上数据采集器 (`custom-scripts/onchain_collector.py`)

**主要修改**：
- 移除了 CryptoQuant API 相关的配置和代码
- 仅保留 Glassnode API 支持
- 更新了类注释和文档字符串
- 修改了指标映射配置

**具体变更**：
```python
# 修改前
class OnchainCollector(BaseCollector):
    """链上数据采集器，支持 CryptoQuant API"""

    CRYPTOQUANT_METRICS = {
        "BTCUSDT": {
            "transaction_volume": "btc_transaction_volume",
            # ...
        }
    }

# 修改后
class OnchainCollector(BaseCollector):
    """链上数据采集器，仅支持 Glassnode API（CryptoQuant 已禁用）"""

    GLASSNODE_METRICS = {
        "BTCUSDT": {
            "transaction_volume": "transactions/count",
            # ...
        }
    }
```

**API 方法更新**：
- `_fetch_cryptoquant_data()` → `_fetch_glassnode_data()`
- 更新了 API 调用逻辑和参数格式
- 修改了数据解析逻辑

### 2. 环境变量配置

**修改文件**：
- `web-ui/env.example`
- `web-ui/docker-compose.yml`

**移除的配置**：
```bash
# 已移除
CRYPTOQUANT_API_KEY=your_cryptoquant_api_key
```

**保留的配置**：
```bash
# 仅保留 Glassnode
GLASSNODE_API_KEY=your_glassnode_api_key
```

### 3. 文档更新

**更新的文档**：
- `README.md`
- `IMPLEMENTATION_SUMMARY.md`
- `agent-docs/API_GUIDE.md`

**主要变更**：
- 移除了 CryptoQuant 相关的说明
- 更新了数据源描述
- 修改了 API 密钥配置说明

## 当前支持的链上数据源

### Glassnode API

**支持的指标**：
- `transactions/count` - 链上交易量
- `addresses/active_count` - 活跃地址数
- `transactions/transfers_volume_exchanges_net` - 交易所净流入
- `market/mvrv` - MVRV 比率

**配置要求**：
```bash
# 环境变量
GLASSNODE_API_KEY=your_glassnode_api_key
```

**API 限制**：
- 免费层：每月 1000 次请求
- 付费层：根据订阅计划

## 数据获取流程

### 1. 初始化采集器

```python
from custom_scripts.onchain_collector import OnchainCollector

collector = OnchainCollector(
    save_dir="data/onchain",
    start="2024-01-01",
    end="2024-01-15"
)
```

### 2. 获取链上数据

```python
# 获取 BTC 链上数据
btc_data = collector.get_data(
    symbol="BTCUSDT",
    interval="1d",
    start_datetime=pd.Timestamp("2024-01-01"),
    end_datetime=pd.Timestamp("2024-01-15")
)
```

### 3. 数据格式

返回的数据包含以下列：
- `date` - 日期
- `transaction_volume` - 链上交易量
- `active_addresses` - 活跃地址数
- `exchange_netflow` - 交易所净流入
- `mvrv_ratio` - MVRV 比率

## 模拟数据模式

当没有配置 Glassnode API 密钥时，系统会自动使用模拟数据：

```python
# 自动检测并切换到模拟模式
if not self.api_key:
    logger.warning("GLASSNODE_API_KEY not found in environment variables")
    logger.info("Using mock data for development")
    return self._generate_mock_data(symbol, start_datetime, end_datetime)
```

## 迁移指南

### 从 CryptoQuant 迁移到 Glassnode

如果您之前使用 CryptoQuant，请按以下步骤迁移：

1. **获取 Glassnode API 密钥**
   - 访问 [Glassnode](https://glassnode.com/)
   - 注册账户并获取 API 密钥

2. **更新环境变量**
   ```bash
   # 移除
   CRYPTOQUANT_API_KEY=your_old_key

   # 添加
   GLASSNODE_API_KEY=your_new_key
   ```

3. **验证数据获取**
   ```bash
   # 测试链上数据采集
   python custom-scripts/onchain_collector.py
   ```

## 注意事项

1. **API 限制**：Glassnode 有请求频率限制，请合理使用
2. **数据延迟**：链上数据通常有 1-2 天的延迟
3. **数据质量**：建议定期检查数据完整性和准确性
4. **成本考虑**：Glassnode 付费服务提供更多数据指标

## 故障排除

### 常见问题

1. **API 密钥无效**
   ```
   Error: Invalid API key
   ```
   **解决方案**：检查 Glassnode API 密钥是否正确配置

2. **请求频率超限**
   ```
   Error: Rate limit exceeded
   ```
   **解决方案**：增加请求延迟或升级 API 计划

3. **数据为空**
   ```
   Warning: No data in response
   ```
   **解决方案**：检查时间范围和资产符号是否正确

### 调试模式

启用详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 未来计划

1. **多数据源支持**：考虑集成其他链上数据提供商
2. **数据缓存**：实现本地数据缓存以减少 API 调用
3. **实时数据**：支持实时链上数据流
4. **更多指标**：添加更多链上分析指标

---

**注意**：CryptoQuant 集成已被永久禁用。如需恢复，请联系开发团队。
