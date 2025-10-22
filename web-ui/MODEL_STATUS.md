# 模型训练状态说明

## ✅ 可用模型

以下模型已测试并可正常训练：

### 1. LGBModel（LightGBM）
- **状态**: ✅ 正常工作
- **描述**: LightGBM 梯度提升决策树模型，适合处理表格数据
- **优点**: 训练速度快、内存占用少、准确率高
- **推荐场景**: 加密货币价格预测、特征工程后的数据
- **测试结果**: 训练成功，无错误

### 2. XGBModel（XGBoost）
- **状态**: ✅ 正常工作
- **描述**: XGBoost 极端梯度提升模型
- **优点**: 强大的特征选择能力、良好的泛化性能
- **推荐场景**: 复杂的非线性关系、竞赛级别的预测任务
- **测试结果**: 训练成功，无错误

### 3. CatBoostModel
- **状态**: ✅ 正常工作
- **描述**: CatBoost 梯度提升模型
- **优点**: 自动处理类别变量、内置正则化、抗过拟合
- **推荐场景**: 表格数据、包含类别特征的数据集
- **测试结果**: 训练成功，无错误
- **注意**: 已修复verbose参数冲突问题

## ⚠️ 不可用模型

### 1. LSTM（长短期记忆网络）
- **状态**: ⚠️ 暂不可用
- **问题**:
  - 训练过程中产生NaN值
  - 特征维度不匹配（期望6个特征，实际184个）
  - Qlib LSTM模型在所有loss为NaN时存在bug
- **错误信息**: `UnboundLocalError: local variable 'best_param' referenced before assignment`
- **根本原因**:
  1. 数据质量问题导致loss为NaN
  2. 特征数量与LSTM期望的d_feat不匹配
  3. 可能需要专门的序列数据处理器
- **计划修复**: 需要创建LSTM专用的数据handler或调整特征工程流程

### 2. Transformer
- **状态**: ⚠️ 未测试
- **说明**: 与LSTM类似，可能存在相同的数据格式问题
- **建议**: 在LSTM问题解决后再测试

## 📊 推荐使用方案

### 初学者推荐
1. **LGBModel** - 最容易上手，训练速度快
2. **XGBModel** - 如果LGB效果不够好，可以尝试XGB

### 生产环境推荐
1. **LGBModel** - 平衡性能和速度
2. **CatBoostModel** - 如果数据包含类别特征
3. **XGBModel** - 需要最佳性能时

### 不建议
- **LSTM/Transformer** - 目前暂不可用，等待修复

## 🔧 故障排查

如果遇到训练失败，请检查：

1. **数据是否存在**
   ```bash
   docker exec crypto_trading_backend ls -la ~/.qlib/qlib_data/crypto_data/features/
   ```

2. **查看训练日志**
   ```bash
   docker logs crypto_trading_backend --tail 100
   ```

3. **检查模型状态**
   - 访问前端界面：http://localhost:8080
   - 进入"模型训练" → "训练进度"标签页
   - 查看详细的错误信息

## 📝 更新日志

- **2025-10-21**:
  - ✅ 修复process_type配置问题（crypto_enhanced_handler.py）
  - ✅ 修复config字段显示unknown问题（qlib_service.py）
  - ✅ 修复XGBModel模块路径错误：`qlib.contrib.model.gbdt` → `qlib.contrib.model.xgboost`
  - ✅ 修复CatBoost模块路径错误：`qlib.contrib.model.gbdt` → `qlib.contrib.model.catboost_model`
  - ✅ 修复CatBoost verbose参数冲突（移除verbose参数）
  - ✅ 修复CatBoost depth/max_depth参数冲突（使用max_depth并移除max_leaves）
  - ✅ **所有树模型（LGBModel、XGBModel、CatBoostModel）全部测试通过**
  - ⚠️ 发现LSTM模型数据兼容性问题（训练loss为NaN）

