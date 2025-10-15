#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Live Trading Strategy for Crypto Trading System
Implements real-time trading strategy with model predictions and risk management
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta
import time
import json
import pickle

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

from gate_executor import GateExecutor, create_gate_executor
from risk_manager import RiskManager, RiskLimits, create_risk_manager
from model_manager import ModelManager

try:
    import qlib
    from qlib.workflow import R
    from qlib.data import D
    QLIB_AVAILABLE = True
except ImportError:
    QLIB_AVAILABLE = False
    logger.warning("Qlib not available. Some features will be disabled.")


class LiveTradingStrategy:
    """实盘交易策略"""

    def __init__(
        self,
        model_name: str = "lgb",
        executor: GateExecutor = None,
        risk_manager: RiskManager = None,
        config: Dict[str, Any] = None
    ):
        """
        初始化实盘交易策略

        Parameters
        ----------
        model_name: str
            模型名称
        executor: GateExecutor
            交易执行器
        risk_manager: RiskManager
            风险管理器
        config: Dict[str, Any]
            配置参数
        """
        self.model_name = model_name
        self.executor = executor or create_gate_executor()
        self.risk_manager = risk_manager or create_risk_manager()
        self.model_manager = ModelManager()

        # 配置参数
        self.config = config or self._get_default_config()

        # 交易状态
        self.is_running = False
        self.last_prediction_time = None
        self.last_trade_time = None
        self.trading_logs = []
        self.performance_metrics = {}

        # 模型相关
        self.model = None
        self.feature_handler = None

        # 初始化 Qlib
        if QLIB_AVAILABLE:
            self._init_qlib()

        logger.info(f"LiveTradingStrategy initialized with model: {model_name}")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "trading_enabled": True,
            "max_positions": 2,
            "position_size": 0.3,
            "rebalance_frequency": "daily",  # daily, weekly
            "prediction_threshold": 0.02,  # 预测信号阈值
            "min_confidence": 0.6,  # 最小置信度
            "stop_loss": 0.05,
            "take_profit": 0.15,
            "max_drawdown": 0.2,
            "data_update_interval": 3600,  # 数据更新间隔（秒）
            "prediction_interval": 86400,  # 预测间隔（秒）
        }

    def _init_qlib(self):
        """初始化 Qlib"""
        try:
            qlib.init(
                provider_uri="~/.qlib/qlib_data/crypto_data",
                region="cn"
            )
            logger.info("Qlib initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Qlib: {e}")

    def start_trading(self) -> Dict[str, Any]:
        """启动交易"""
        try:
            if self.is_running:
                return {"success": False, "error": "Trading is already running"}

            # 加载模型
            model_loaded = self._load_model()
            if not model_loaded:
                return {"success": False, "error": "Failed to load model"}

            # 检查交易状态
            trading_status = self.executor.get_trading_status()
            if not trading_status["trading_enabled"]:
                return {"success": False, "error": "Trading not enabled on exchange"}

            # 启动交易
            self.is_running = True
            self._log_trading_event("TRADING_STARTED", "Trading strategy started")

            # 执行初始交易
            self._run_trading_cycle()

            return {
                "success": True,
                "message": "Trading started successfully",
                "config": self.config
            }

        except Exception as e:
            logger.error(f"Error starting trading: {e}")
            return {"success": False, "error": str(e)}

    def stop_trading(self) -> Dict[str, Any]:
        """停止交易"""
        try:
            if not self.is_running:
                return {"success": False, "error": "Trading is not running"}

            # 停止交易
            self.is_running = False
            self._log_trading_event("TRADING_STOPPED", "Trading strategy stopped")

            return {
                "success": True,
                "message": "Trading stopped successfully"
            }

        except Exception as e:
            logger.error(f"Error stopping trading: {e}")
            return {"success": False, "error": str(e)}

    def _load_model(self) -> bool:
        """加载模型"""
        try:
            if not QLIB_AVAILABLE:
                logger.warning("Qlib not available, using mock model")
                self.model = MockModel()
                return True

            # 从 MLflow 加载最新模型
            exp = R.get_exp(experiment_name="workflow")
            recorders = exp.list_recorders()

            if not recorders:
                logger.error("No trained models found")
                return False

            # 获取最新的 recorder
            latest_recorder = recorders.iloc[-1]
            recorder_id = latest_recorder['id']
            recorder = R.get_recorder(recorder_id=recorder_id, experiment_name="workflow")

            # 加载模型
            self.model = recorder.load_object("model.pkl")
            logger.info(f"Model loaded successfully: {recorder_id}")

            return True

        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False

    def _run_trading_cycle(self) -> Dict[str, Any]:
        """运行交易周期"""
        try:
            # 1. 获取最新数据
            latest_data = self._fetch_latest_data()
            if latest_data.empty:
                return {"success": False, "error": "No data available"}

            # 2. 生成预测
            predictions = self._generate_predictions(latest_data)
            if predictions.empty:
                return {"success": False, "error": "No predictions generated"}

            # 3. 生成交易信号
            signals = self._generate_trading_signals(predictions)
            if not signals:
                return {"success": True, "message": "No trading signals generated"}

            # 4. 风险控制检查
            filtered_signals = self._apply_risk_controls(signals)
            if not filtered_signals:
                return {"success": True, "message": "All signals filtered by risk controls"}

            # 5. 执行交易
            execution_results = self._execute_trades(filtered_signals)

            # 6. 更新状态
            self._update_trading_state(execution_results)

            return {
                "success": True,
                "signals_generated": len(signals),
                "signals_executed": len(filtered_signals),
                "execution_results": execution_results
            }

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
            return {"success": False, "error": str(e)}

    def _fetch_latest_data(self) -> pd.DataFrame:
        """获取最新数据"""
        try:
            if not QLIB_AVAILABLE:
                # 返回模拟数据
                return self._generate_mock_data()

            # 获取最新数据
            instruments = ["btcusdt", "ethusdt"]
            end_time = datetime.now().strftime("%Y-%m-%d")
            start_time = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")

            data = D.features(
                instruments=instruments,
                fields=["$open", "$high", "$low", "$close", "$volume", "$vwap"],
                start_time=start_time,
                end_time=end_time,
                freq="day"
            )

            return data.reset_index()

        except Exception as e:
            logger.error(f"Error fetching latest data: {e}")
            return pd.DataFrame()

    def _generate_predictions(self, data: pd.DataFrame) -> pd.DataFrame:
        """生成预测"""
        try:
            if self.model is None:
                logger.error("Model not loaded")
                return pd.DataFrame()

            # 准备特征数据
            features = self._prepare_features(data)
            if features.empty:
                return pd.DataFrame()

            # 生成预测
            predictions = self.model.predict(features)

            # 格式化预测结果
            pred_df = pd.DataFrame({
                'instrument': features.index.get_level_values('instrument'),
                'date': features.index.get_level_values('datetime'),
                'prediction': predictions,
                'confidence': np.abs(predictions)  # 简单的置信度计算
            })

            self.last_prediction_time = datetime.now()
            logger.info(f"Generated {len(pred_df)} predictions")

            return pred_df

        except Exception as e:
            logger.error(f"Error generating predictions: {e}")
            return pd.DataFrame()

    def _generate_trading_signals(self, predictions: pd.DataFrame) -> List[Dict[str, Any]]:
        """生成交易信号"""
        try:
            signals = []

            for _, row in predictions.iterrows():
                instrument = row['instrument']
                prediction = row['prediction']
                confidence = row['confidence']

                # 检查预测阈值和置信度
                if confidence < self.config["min_confidence"]:
                    continue

                if abs(prediction) < self.config["prediction_threshold"]:
                    continue

                # 生成信号
                signal = {
                    "instrument": instrument,
                    "action": "buy" if prediction > 0 else "sell",
                    "confidence": confidence,
                    "prediction": prediction,
                    "timestamp": datetime.now().isoformat()
                }

                signals.append(signal)

            logger.info(f"Generated {len(signals)} trading signals")
            return signals

        except Exception as e:
            logger.error(f"Error generating trading signals: {e}")
            return []

    def _apply_risk_controls(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """应用风险控制"""
        try:
            filtered_signals = []

            # 获取当前持仓和余额
            positions = self.executor.get_positions()
            balance = self.executor.get_balance()
            portfolio_value = sum(balance.values())

            for signal in signals:
                # 检查仓位限制
                position_check = self.risk_manager.check_position_limit(
                    signal["instrument"],
                    signal.get("amount", 0.1),  # 默认数量
                    signal.get("price", 50000),  # 默认价格
                    portfolio_value
                )

                if not position_check["allowed"]:
                    logger.warning(f"Signal filtered by position limit: {position_check['reason']}")
                    continue

                # 检查回撤限制
                current_value = portfolio_value
                peak_value = max(self.risk_manager.portfolio_history) if self.risk_manager.portfolio_history else current_value

                drawdown_check = self.risk_manager.check_drawdown(current_value, peak_value)
                if not drawdown_check["allowed"]:
                    logger.warning(f"Signal filtered by drawdown limit: {drawdown_check['reason']}")
                    continue

                # 检查日亏损限制
                daily_pnl = self.risk_manager._calculate_daily_pnl()
                daily_loss_check = self.risk_manager.check_daily_loss(daily_pnl, portfolio_value)
                if not daily_loss_check["allowed"]:
                    logger.warning(f"Signal filtered by daily loss limit: {daily_loss_check['reason']}")
                    continue

                filtered_signals.append(signal)

            logger.info(f"Risk controls filtered {len(signals) - len(filtered_signals)} signals")
            return filtered_signals

        except Exception as e:
            logger.error(f"Error applying risk controls: {e}")
            return []

    def _execute_trades(self, signals: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """执行交易"""
        try:
            execution_results = []

            for signal in signals:
                try:
                    # 获取当前价格
                    currency_pair = self._get_currency_pair(signal["instrument"])
                    market_data = self.executor.get_market_data(currency_pair)

                    if "error" in market_data:
                        logger.error(f"Error getting market data: {market_data['error']}")
                        continue

                    current_price = market_data["last_price"]

                    # 计算交易数量
                    balance = self.executor.get_balance()
                    portfolio_value = sum(balance.values())

                    if signal["action"] == "buy":
                        # 买入：使用 USDT 余额
                        available_usdt = balance.get("USDT", 0)
                        amount = (available_usdt * self.config["position_size"]) / current_price
                    else:
                        # 卖出：使用币种余额
                        base_currency = signal["instrument"].replace("USDT", "")
                        available_amount = balance.get(base_currency, 0)
                        amount = available_amount * self.config["position_size"]

                    # 执行订单
                    order_result = self.executor.place_order(
                        currency_pair=currency_pair,
                        side=signal["action"],
                        amount=amount,
                        price=current_price,
                        order_type="limit"
                    )

                    execution_results.append({
                        "signal": signal,
                        "order_result": order_result,
                        "timestamp": datetime.now().isoformat()
                    })

                    if order_result["success"]:
                        self._log_trading_event("ORDER_EXECUTED", f"Order {order_result['order_id']} executed")
                    else:
                        self._log_trading_event("ORDER_FAILED", f"Order failed: {order_result['error']}")

                except Exception as e:
                    logger.error(f"Error executing trade for {signal['instrument']}: {e}")
                    execution_results.append({
                        "signal": signal,
                        "order_result": {"success": False, "error": str(e)},
                        "timestamp": datetime.now().isoformat()
                    })

            self.last_trade_time = datetime.now()
            return execution_results

        except Exception as e:
            logger.error(f"Error executing trades: {e}")
            return []

    def _update_trading_state(self, execution_results: List[Dict[str, Any]]):
        """更新交易状态"""
        try:
            # 更新持仓
            positions = self.executor.get_positions()
            self.risk_manager.positions = {
                pos["currency"]: pos for pos in positions
            }

            # 更新组合价值
            balance = self.executor.get_balance()
            portfolio_value = sum(balance.values())
            self.risk_manager.update_portfolio_value(portfolio_value)

            # 计算并更新收益
            if len(self.risk_manager.portfolio_history) >= 2:
                daily_pnl = self.risk_manager.portfolio_history[-1] - self.risk_manager.portfolio_history[-2]
                self.risk_manager.update_daily_pnl(daily_pnl)

            # 更新性能指标
            self._update_performance_metrics(execution_results)

        except Exception as e:
            logger.error(f"Error updating trading state: {e}")

    def _update_performance_metrics(self, execution_results: List[Dict[str, Any]]):
        """更新性能指标"""
        try:
            # 计算基本指标
            total_signals = len(execution_results)
            successful_orders = sum(1 for result in execution_results if result["order_result"]["success"])

            self.performance_metrics.update({
                "total_signals": total_signals,
                "successful_orders": successful_orders,
                "success_rate": successful_orders / total_signals if total_signals > 0 else 0,
                "last_update": datetime.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error updating performance metrics: {e}")

    def _prepare_features(self, data: pd.DataFrame) -> pd.DataFrame:
        """准备特征数据"""
        try:
            # 这里应该实现特征准备逻辑
            # 包括特征工程、标准化等
            # 为了简化，返回原始数据
            return data

        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            return pd.DataFrame()

    def _get_currency_pair(self, instrument: str) -> str:
        """获取交易对格式"""
        if instrument.endswith("USDT"):
            base = instrument[:-4]
            return f"{base}_USDT"
        else:
            return instrument

    def _generate_mock_data(self) -> pd.DataFrame:
        """生成模拟数据"""
        dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq="D")
        instruments = ["btcusdt", "ethusdt"]

        data = []
        for instrument in instruments:
            for date in dates:
                data.append({
                    "instrument": instrument,
                    "datetime": date,
                    "open": 50000 + np.random.normal(0, 1000),
                    "high": 51000 + np.random.normal(0, 1000),
                    "low": 49000 + np.random.normal(0, 1000),
                    "close": 50000 + np.random.normal(0, 1000),
                    "volume": 1000000 + np.random.normal(0, 100000),
                    "vwap": 50000 + np.random.normal(0, 1000)
                })

        return pd.DataFrame(data)

    def _log_trading_event(self, event_type: str, message: str):
        """记录交易事件"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message
        }

        self.trading_logs.append(log_entry)
        logger.info(f"Trading Event [{event_type}]: {message}")

    def get_trading_status(self) -> Dict[str, Any]:
        """获取交易状态"""
        return {
            "is_running": self.is_running,
            "model_name": self.model_name,
            "last_prediction_time": self.last_prediction_time.isoformat() if self.last_prediction_time else None,
            "last_trade_time": self.last_trade_time.isoformat() if self.last_trade_time else None,
            "total_logs": len(self.trading_logs),
            "performance_metrics": self.performance_metrics,
            "config": self.config
        }

    def get_trading_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取交易日志"""
        return self.trading_logs[-limit:] if limit > 0 else self.trading_logs

    def get_performance_report(self) -> Dict[str, Any]:
        """获取性能报告"""
        try:
            # 计算风险指标
            positions = self.executor.get_positions()
            balance = self.executor.get_balance()
            portfolio_value = sum(balance.values())

            risk_metrics = self.risk_manager.calculate_risk_metrics(
                {pos["currency"]: pos for pos in positions},
                portfolio_value
            )

            # 生成风险报告
            risk_report = self.risk_manager.generate_risk_report(risk_metrics)

            return {
                "trading_status": self.get_trading_status(),
                "performance_metrics": self.performance_metrics,
                "risk_report": risk_report,
                "positions": positions,
                "balance": balance,
                "portfolio_value": portfolio_value
            }

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            return {"error": str(e)}


class MockModel:
    """模拟模型（用于测试）"""

    def predict(self, features):
        """生成模拟预测"""
        n_samples = len(features) if hasattr(features, '__len__') else 1
        return np.random.normal(0, 0.1, n_samples)


def create_live_trading_strategy(
    model_name: str = "lgb",
    config: Dict[str, Any] = None
) -> LiveTradingStrategy:
    """创建实盘交易策略

    Parameters
    ----------
    model_name: str
        模型名称
    config: Dict[str, Any]
        配置参数

    Returns
    -------
    LiveTradingStrategy
        交易策略实例
    """
    return LiveTradingStrategy(model_name=model_name, config=config)


if __name__ == "__main__":
    # 测试实盘交易策略
    strategy = create_live_trading_strategy()

    # 获取交易状态
    status = strategy.get_trading_status()
    print(f"Trading Status: {status}")

    # 启动交易（仅用于测试）
    # result = strategy.start_trading()
    # print(f"Start Trading Result: {result}")

    # 获取性能报告
    report = strategy.get_performance_report()
    print(f"Performance Report: {report}")

