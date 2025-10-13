# 加密货币量化交易系统 - 环境配置和操作指南

## 1. 环境配置

### 1.1 系统要求

- **操作系统**: Linux (Ubuntu 22.04 推荐)
- **Python版本**: Python 3.11
- **内存**: 建议 4GB 以上
- **存储**: 至少 2GB 可用空间

### 1.2 安装 Python 3.11

```bash
# 更新软件包列表
sudo apt-get update

# 安装 Python 3.11 及相关工具
sudo apt-get install -y python3.11 python3.11-venv python3.11-dev

# 验证安装
python3.11 --version
```

### 1.3 创建虚拟环境

```bash
# 进入项目目录
cd /root/myrepo/qlib

# 创建虚拟环境
python3.11 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 升级 pip
pip install --upgrade pip
```

### 1.4 安装项目依赖

```bash
# 安装前置依赖
pip install numpy cython

# 安装 Qlib (从源码)
pip install -e .

# 安装 Gate.io API 客户端
pip install gate-api

# 安装其他必要依赖（如果未包含在 Qlib 依赖中）
pip install python-dotenv matplotlib
```

## 2. API 配置

### 2.1 创建 .env 文件

在项目根目录创建 `.env` 文件（如果需要使用认证API）：

```bash
# Gate.io API 配置（公开数据不需要）
GATE_API_KEY=your_api_key_here
GATE_API_SECRET=your_api_secret_here
```

**注意**: 本项目使用 Gate.io 公开API获取K线数据，不需要API密钥。如果需要访问私有API（如交易功能），才需要配置密钥。

## 3. 数据拉取

### 3.1 拉取原始数据

```bash
# 激活虚拟环境
source venv/bin/activate

# 运行数据采集器
python custom-scripts/gate_collector.py download_data \
  --source_dir /root/myrepo/qlib/data/gate/source \
  --start 2024-01-01 \
  --end 2025-10-12 \
  --delay 0.5
```

**参数说明**:
- `--source_dir`: 原始数据保存目录
- `--start`: 开始日期 (YYYY-MM-DD)
- `--end`: 结束日期 (YYYY-MM-DD)
- `--delay`: API请求延迟（秒），建议0.2-0.5

### 3.2 标准化数据

```bash
python custom-scripts/gate_collector.py normalize_data \
  --source_dir /root/myrepo/qlib/data/gate/source \
  --normalize_dir /root/myrepo/qlib/data/gate/normalize
```

### 3.3 转换为 Qlib 格式

```bash
python scripts/dump_bin.py dump_all \
  --data_path data/gate/normalize \
  --qlib_dir ~/.qlib/qlib_data/crypto_data \
  --include_fields open,close,high,low,volume \
  --symbol_field_name symbol \
  --date_field_name date \
  --freq day
```

### 3.4 验证数据

```bash
# 检查数据目录结构
ls -lh ~/.qlib/qlib_data/crypto_data/

# 查看生成的交易对列表
cat ~/.qlib/qlib_data/crypto_data/instruments/all.txt

# 查看日历文件
head ~/.qlib/qlib_data/crypto_data/calendars/day.txt
```

## 4. 运行回测

### 4.1 使用配置文件运行

```bash
# 确保在 custom-scripts 目录下
cd custom-scripts

# 运行训练和回测
qrun crypto_workflow_config.yaml
```

### 4.2 配置文件说明

`crypto_workflow_config.yaml` 主要配置项：

- **qlib_init**: Qlib初始化参数
  - `provider_uri`: 数据目录路径
  - `region`: 区域设置（cn）

- **data_handler_config**: 数据处理配置
  - `start_time`/`end_time`: 数据时间范围
  - `instruments`: 交易对列表
  - `infer_processors`: 特征处理器
  - `learn_processors`: 标签处理器

- **task.model**: 模型配置（LightGBM）
  - 各种超参数设置

- **task.dataset**: 数据集划分
  - `train`: 训练集时间范围
  - `valid`: 验证集时间范围
  - `test`: 测试集时间范围

- **port_analysis_config**: 回测配置
  - `strategy`: 交易策略
  - `backtest`: 回测参数（账户金额、交易成本等）

## 5. 生成报告

```bash
# 生成 Markdown 格式的回测报告
python custom-scripts/generate_report_simple.py
```

报告将生成在 `agent-docs/` 目录下：
- `backtest_report.md`: 详细的回测分析报告
- `returns_curve.png`: 收益曲线图

## 6. 目录结构

```
/root/myrepo/qlib/
├── custom-scripts/          # 自定义脚本
│   ├── gate_collector.py          # Gate.io数据采集器
│   ├── crypto_workflow_config.yaml # 训练回测配置
│   └── generate_report_simple.py  # 报告生成脚本
├── agent-docs/              # 文档和报告
│   ├── setup_guide.md             # 本文档
│   ├── backtest_report.md         # 回测报告
│   ├── project_summary.md         # 项目总结
│   └── returns_curve.png          # 收益曲线图
├── data/gate/               # 原始和标准化数据
│   ├── source/                    # Gate.io原始数据
│   └── normalize/                 # 标准化数据
└── venv/                    # Python虚拟环境

~/.qlib/qlib_data/crypto_data/ # Qlib二进制数据
├── calendars/               # 交易日历
├── instruments/             # 交易对列表
└── features/                # 特征数据
    ├── btcusdt/
    └── ethusdt/
```

## 7. 常见问题

### Q1: 数据下载失败

**A**: 检查网络连接，确保可以访问 Gate.io API。如果频繁请求导致限流，增加 `--delay` 参数值。

```bash
# 增加延迟到1秒
python custom-scripts/gate_collector.py download_data --delay 1.0 ...
```

### Q2: 回测报错：IndexError

**A**: 检查配置文件中的日期范围是否超出实际数据范围。确保：
- 测试集结束日期不晚于最新数据日期
- 训练集、验证集、测试集时间不重叠

### Q3: 模型训练收敛

**A**: 如果看到 "Early stopping, best iteration is [1]"，说明模型很快收敛。这可能是因为：
- 样本数量较少（仅2个交易对）
- 特征相关性高
- 标签信号较弱

可以尝试：
- 增加更多交易对
- 调整模型超参数
- 使用更复杂的模型（如深度学习模型）

### Q4: 中文字体显示问题

**A**: 在生成图表时可能出现中文字体警告。图表仍会正常生成，只是中文标签可能显示为方块。

解决方法：
```bash
# 安装中文字体
sudo apt-get install fonts-wqy-zenhei

# 或配置 matplotlib 使用系统字体
# 修改 ~/.config/matplotlib/matplotlibrc
```

### Q5: 内存不足

**A**: 如果系统内存有限，可以：
- 减少特征数量
- 缩短训练数据时间范围
- 增加系统交换空间

## 8. 进阶使用

### 8.1 修改交易对

编辑 `custom-scripts/gate_collector.py` 中的 `SUPPORTED_PAIRS` 列表：

```python
SUPPORTED_PAIRS = ["ETH_USDT", "BTC_USDT", "SOL_USDT", "BNB_USDT"]
```

### 8.2 调整模型参数

编辑 `crypto_workflow_config.yaml` 中的模型配置：

```yaml
task:
    model:
        kwargs:
            learning_rate: 0.05  # 学习率
            max_depth: 8         # 树深度
            num_leaves: 210      # 叶子节点数
            ...
```

### 8.3 更换模型

Qlib 支持多种模型。要使用其他模型，修改配置文件：

```yaml
task:
    model:
        class: XGBModel  # 或 LGBModel, CatBoostModel等
        module_path: qlib.contrib.model.gbdt
```

## 9. 性能优化建议

1. **数据层面**:
   - 使用更长的历史数据
   - 增加更多交易对以提高样本多样性
   - 考虑使用分钟级数据

2. **特征层面**:
   - 增加加密货币特有特征（链上数据、情绪指标）
   - 进行特征选择，去除冗余特征
   - 尝试时序特征工程

3. **模型层面**:
   - 尝试深度学习模型（LSTM、Transformer）
   - 使用集成学习方法
   - 进行超参数优化

4. **策略层面**:
   - 优化仓位管理
   - 增加风险控制措施
   - 考虑市场状态切换

## 10. 技术支持

- **Qlib 官方文档**: https://qlib.readthedocs.io/
- **Gate.io API 文档**: https://www.gate.io/docs/developers/apiv4
- **项目 GitHub**: https://github.com/microsoft/qlib

---

*最后更新: 2025-10-13*

