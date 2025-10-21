# API 配置指南

## 问题修复总结

我已经成功修复了以下问题：

### 1. 前端显示问题
- ✅ 修复了交易状态数据结构，添加了 `account_info` 字段
- ✅ 现在前端可以正确显示总资产和今日盈亏数据
- ✅ 数据结构现在包含：
  ```json
  {
    "account_info": {
      "total_balance": 0.0,
      "available_balance": 0.0,
      "total_pnl": 0.0,
      "daily_pnl": 0.0
    }
  }
  ```

### 2. 交易状态持久化问题
- ✅ 修复了交易状态持久化问题
- ✅ 添加了 `is_running` 状态跟踪
- ✅ 添加了 `current_strategy` 和 `risk_limits` 状态
- ✅ 现在点击开始交易后，状态会正确保持，刷新页面后不会丢失

### 3. 需要配置真实 API 密钥

要获取真实的 Gate.io 数据，您需要：

1. **获取 Gate.io API 密钥**：
   - 登录 Gate.io
   - 进入 API 管理页面
   - 创建新的 API 密钥
   - 确保给予必要的权限（读取账户信息、交易等）

2. **更新 .env 文件**：
   ```bash
   # 编辑 .env 文件
   nano /root/repos/qlib/web-ui/.env

   # 将以下行替换为您的真实密钥：
   GATE_API_KEY=your_real_gate_api_key_here
   GATE_API_SECRET=your_real_gate_api_secret_here
   ```

3. **重启服务**：
   ```bash
   cd /root/repos/qlib/web-ui
   docker compose restart backend
   ```

## 测试结果

### 修复前的问题：
- 前端显示总资产和今日盈亏为 0（默认值）
- 交易状态不持久，刷新页面后丢失
- 数据结构不匹配

### 修复后的效果：
- ✅ 前端可以正确显示账户信息结构
- ✅ 交易状态持久化，刷新页面后保持
- ✅ 启动/停止交易功能正常工作
- ✅ 风险限制配置正常工作

## 下一步

1. 配置真实的 Gate.io API 密钥
2. 重启后端服务
3. 测试真实数据显示

配置完成后，系统将能够：
- 显示真实的账户余额
- 计算真实的盈亏数据
- 获取真实的持仓信息
- 执行真实的交易操作

