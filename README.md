# 加密货币量化交易系统

基于 Qlib 的加密货币量化交易系统，集成了链上数据、新闻情绪分析、多模型支持、Web UI 和实盘交易功能。

## 🚀 主要特性

### 📊 数据增强
- **价格数据**: Gate.io API 实时价格数据
- **链上数据**: 已完全移除（不影响其他功能）
- **新闻情绪**: CryptoPanic API + FinBERT 情绪分析
- **数据融合**: 多源数据统一处理和特征工程

### 🤖 模型管理
- **多模型支持**: LightGBM、XGBoost、CatBoost、LSTM、Transformer
- **参数调优**: Optuna 超参数优化
- **模型切换**: 动态模型选择和配置
- **性能监控**: 模型性能指标跟踪

### 🌐 Web 界面
- **仪表盘**: 实时收益曲线、关键指标展示
- **数据管理**: 数据更新状态、手动触发采集
- **模型训练**: 模型选择、参数配置、训练监控
- **回测面板**: 回测配置、结果可视化
- **实盘交易**: 交易控制、持仓监控、风险设置

### 💰 实盘交易
- **Gate.io 集成**: 真实交易执行
- **风险管理**: 仓位限制、止损、回撤控制
- **定时调度**: 自动化数据采集和交易执行
- **监控告警**: 实时风险监控和异常告警

## 📁 项目结构

```
qlib/
├── custom-scripts/           # 核心脚本
│   ├── gate_collector.py     # 价格数据采集
│   ├── onchain_collector.py  # 链上数据采集
│   ├── news_collector.py     # 新闻数据采集
│   ├── gate_executor.py      # Gate.io 交易执行器
│   ├── risk_manager.py       # 风险管理模块
│   ├── live_trading_strategy.py # 实盘交易策略
│   ├── live_trading_scheduler.py # 定时调度器
│   └── model_configs/        # 模型配置文件
├── web-ui/                   # Web 界面
│   ├── backend/              # Flask 后端
│   ├── frontend/             # React 前端
│   ├── nginx/                # Nginx 配置
│   └── docker-compose.yml    # Docker 部署
├── data/                     # 数据存储
│   ├── gate/                 # 价格数据
│   ├── onchain/              # 链上数据
│   └── news/                 # 新闻数据
└── agent-docs/               # 文档
```

## 🛠️ 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd qlib

# 安装 Python 依赖
pip install -r requirements.txt

# 安装前端依赖
cd web-ui/frontend
npm install
cd ../..
```

### 2. 配置环境变量

  ```bash
# 复制环境变量模板
cp web-ui/env.example web-ui/.env

# 编辑配置文件
nano web-ui/.env
```

配置必要的 API 密钥：
- `GATE_API_KEY`: Gate.io API Key
- `GATE_API_SECRET`: Gate.io API Secret
- `CRYPTOPANIC_API_KEY`: CryptoPanic API Key
- ~~`GLASSNODE_API_KEY`: Glassnode API Key（链上数据已禁用）~~

### 3. 数据准备

    ```bash
# 采集价格数据
python custom-scripts/gate_collector.py

# 链上数据采集已移除

# 采集新闻数据
python custom-scripts/news_collector.py

# 数据融合
python custom-scripts/merge_data.py
```

### 4. 模型训练

```bash
# 使用默认配置训练模型
python -m qlib.run.get_data qlib_sdk --config_path custom-scripts/crypto_workflow_config.yaml
python -m qlib.run.workflow custom-scripts/crypto_workflow_config.yaml
```

### 5. 启动 Web 界面

  ```bash
# 使用 Docker Compose 部署
cd web-ui
./deploy.sh
```

或者手动启动：

  ```bash
# 启动后端
cd web-ui/backend
python app.py

# 启动前端
cd web-ui/frontend
npm start
```

访问 `http://localhost` 查看 Web 界面。

## 📖 使用指南

### 数据管理

1. **数据采集**: 在 Web 界面的数据管理页面手动触发数据采集
2. **数据状态**: 查看各数据源的覆盖范围和最新日期
3. **数据质量**: 检查数据完整性和异常值

### 模型训练

1. **模型选择**: 在模型训练页面选择要使用的模型类型
2. **参数配置**: 调整模型超参数
3. **训练监控**: 实时查看训练进度和性能指标
4. **模型对比**: 比较不同模型的性能表现

### 回测分析

1. **回测配置**: 设置时间范围、初始资金、交易成本
2. **运行回测**: 执行回测并查看结果
3. **结果分析**: 查看收益曲线、回撤图、持仓变化
4. **性能指标**: 分析夏普比率、最大回撤、胜率等指标

### 实盘交易

1. **交易控制**: 启动/停止实盘交易
2. **持仓监控**: 实时查看当前持仓和盈亏
3. **订单管理**: 查看订单历史和状态
4. **风险设置**: 配置仓位限制、止损、回撤控制

## 🔧 配置说明

### 模型配置

模型配置文件位于 `custom-scripts/model_configs/` 目录：

- `lgb_config.yaml`: LightGBM 配置
- `xgb_config.yaml`: XGBoost 配置
- `catboost_config.yaml`: CatBoost 配置
- `lstm_config.yaml`: LSTM 配置
- `transformer_config.yaml`: Transformer 配置

### 风险控制

风险管理配置：

  ```python
risk_limits = {
    "max_position_size": 0.3,      # 单币种最大仓位 30%
    "max_total_exposure": 0.8,     # 总敞口限制 80%
    "max_drawdown": 0.2,           # 最大回撤 20%
    "stop_loss": 0.05,             # 止损线 5%
    "max_daily_loss": 0.05,        # 单日最大亏损 5%
}
```

### 调度配置

定时任务配置：

```python
schedules = {
    "data_collection": {
        "price_data": "0 */6 * * *",    # 每6小时
        "onchain_data": "0 2 * * *",    # 每天凌晨2点
        "news_data": "0 */2 * * *",     # 每2小时
    },
    "trading": {
        "daily_trading": "0 9 * * 1-5", # 工作日早上9点
        "risk_check": "0 */4 * * *",    # 每4小时
    }
}
```

## 📊 监控和告警

### 系统监控

- **Prometheus**: 指标收集和存储
- **Grafana**: 可视化仪表盘
- **日志系统**: 结构化日志记录

### 告警机制

- **风险告警**: 回撤超限、仓位过重
- **系统告警**: 服务异常、数据采集失败
- **交易告警**: 订单失败、余额不足

## 🔒 安全考虑

### API 安全

- 使用环境变量存储敏感信息
- API 密钥定期轮换
- 请求频率限制

### 交易安全

- 沙盒环境测试
- 小额资金试运行
- 多重风险控制

### 数据安全

- 数据加密存储
- 访问权限控制
- 定期备份

## 🐛 故障排除

### 常见问题

1. **数据采集失败**
   - 检查 API 密钥配置
   - 确认网络连接
   - 查看错误日志

2. **模型训练失败**
   - 检查数据完整性
   - 确认内存充足
   - 查看训练日志

3. **交易执行失败**
   - 检查账户余额
   - 确认交易对存在
   - 查看订单状态

### 日志查看

```bash
# 查看服务日志
docker-compose logs -f [service_name]

# 查看应用日志
tail -f logs/app.log

# 查看交易日志
tail -f logs/trading.log
```

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证。详见 [LICENSE](LICENSE) 文件。

## 📞 支持

如有问题或建议，请：

1. 查看 [文档](agent-docs/)
2. 提交 [Issue](issues)
3. 联系维护者

## 🔄 更新日志

### v1.0.0 (2024-01-XX)
- 初始版本发布
- 基础量化交易功能
- Web 界面
- 实盘交易支持

---

**⚠️ 风险提示**: 加密货币交易存在高风险，请谨慎投资，本系统仅供学习和研究使用。
