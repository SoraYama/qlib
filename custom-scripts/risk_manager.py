#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Risk Management Module for Crypto Trading
Implements position limits, stop loss, drawdown control, and other risk measures
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))


class RiskLevel(Enum):
    """风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class RiskLimits:
    """风险限制配置"""
    # 仓位限制
    max_position_size: float = 0.3  # 单币种最大仓位 30%
    max_total_exposure: float = 0.8  # 总敞口限制 80%
    max_correlation_exposure: float = 0.5  # 相关资产敞口限制 50%

    # 回撤控制
    max_drawdown: float = 0.2  # 最大回撤 20%
    max_daily_loss: float = 0.05  # 单日最大亏损 5%
    max_weekly_loss: float = 0.15  # 单周最大亏损 15%

    # 止损设置
    stop_loss: float = 0.05  # 止损线 5%
    trailing_stop: float = 0.03  # 跟踪止损 3%

    # 流动性限制
    min_liquidity: float = 1000000  # 最小流动性 100万 USDT
    max_slippage: float = 0.01  # 最大滑点 1%

    # 其他限制
    max_orders_per_day: int = 100  # 每日最大订单数
    max_order_size: float = 0.1  # 单笔订单最大金额占比 10%


@dataclass
class Position:
    """持仓信息"""
    symbol: str
    amount: float
    entry_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float = 0.0
    realized_pnl: float = 0.0


@dataclass
class RiskMetrics:
    """风险指标"""
    total_portfolio_value: float
    total_exposure: float
    max_drawdown: float
    current_drawdown: float
    daily_pnl: float
    weekly_pnl: float
    sharpe_ratio: float
    var_95: float  # 95% VaR
    cvar_95: float  # 95% CVaR
    concentration_risk: float
    correlation_risk: float


class RiskManager:
    """风险管理器"""

    def __init__(self, risk_limits: RiskLimits = None):
        """
        初始化风险管理器

        Parameters
        ----------
        risk_limits: RiskLimits
            风险限制配置
        """
        self.risk_limits = risk_limits or RiskLimits()
        self.positions = {}  # 当前持仓
        self.daily_pnl_history = []  # 日收益历史
        self.weekly_pnl_history = []  # 周收益历史
        self.portfolio_history = []  # 组合价值历史
        self.risk_alerts = []  # 风险告警

        logger.info("RiskManager initialized")

    def check_position_limit(self, symbol: str, amount: float, price: float, portfolio_value: float) -> Dict[str, Any]:
        """检查仓位限制

        Parameters
        ----------
        symbol: str
            交易对符号
        amount: float
            交易数量
        price: float
            交易价格
        portfolio_value: float
            组合总价值

        Returns
        -------
        Dict[str, Any]
            检查结果
        """
        try:
            # 计算新仓位价值
            position_value = amount * price
            position_ratio = position_value / portfolio_value

            # 检查单币种仓位限制
            if position_ratio > self.risk_limits.max_position_size:
                return {
                    "allowed": False,
                    "reason": f"Position size {position_ratio:.2%} exceeds limit {self.risk_limits.max_position_size:.2%}",
                    "risk_level": RiskLevel.HIGH
                }

            # 检查总敞口限制
            current_exposure = self._calculate_total_exposure(portfolio_value)
            new_exposure = current_exposure + position_ratio

            if new_exposure > self.risk_limits.max_total_exposure:
                return {
                    "allowed": False,
                    "reason": f"Total exposure {new_exposure:.2%} exceeds limit {self.risk_limits.max_total_exposure:.2%}",
                    "risk_level": RiskLevel.HIGH
                }

            # 检查单笔订单限制
            if position_ratio > self.risk_limits.max_order_size:
                return {
                    "allowed": False,
                    "reason": f"Order size {position_ratio:.2%} exceeds limit {self.risk_limits.max_order_size:.2%}",
                    "risk_level": RiskLevel.MEDIUM
                }

            return {
                "allowed": True,
                "position_ratio": position_ratio,
                "risk_level": RiskLevel.LOW
            }

        except Exception as e:
            logger.error(f"Error checking position limit: {e}")
            return {
                "allowed": False,
                "reason": f"Error in position limit check: {str(e)}",
                "risk_level": RiskLevel.CRITICAL
            }

    def check_drawdown(self, current_value: float, peak_value: float) -> Dict[str, Any]:
        """检查回撤限制

        Parameters
        ----------
        current_value: float
            当前组合价值
        peak_value: float
            历史峰值

        Returns
        -------
        Dict[str, Any]
            检查结果
        """
        try:
            if peak_value <= 0:
                return {"allowed": True, "drawdown": 0.0, "risk_level": RiskLevel.LOW}

            # 计算当前回撤
            current_drawdown = (peak_value - current_value) / peak_value

            # 检查最大回撤限制
            if current_drawdown > self.risk_limits.max_drawdown:
                return {
                    "allowed": False,
                    "reason": f"Current drawdown {current_drawdown:.2%} exceeds limit {self.risk_limits.max_drawdown:.2%}",
                    "drawdown": current_drawdown,
                    "risk_level": RiskLevel.CRITICAL
                }

            # 检查风险等级
            if current_drawdown > self.risk_limits.max_drawdown * 0.8:
                risk_level = RiskLevel.HIGH
            elif current_drawdown > self.risk_limits.max_drawdown * 0.6:
                risk_level = RiskLevel.MEDIUM
            else:
                risk_level = RiskLevel.LOW

            return {
                "allowed": True,
                "drawdown": current_drawdown,
                "risk_level": risk_level
            }

        except Exception as e:
            logger.error(f"Error checking drawdown: {e}")
            return {
                "allowed": False,
                "reason": f"Error in drawdown check: {str(e)}",
                "risk_level": RiskLevel.CRITICAL
            }

    def check_daily_loss(self, daily_pnl: float, portfolio_value: float) -> Dict[str, Any]:
        """检查日亏损限制

        Parameters
        ----------
        daily_pnl: float
            日收益
        portfolio_value: float
            组合价值

        Returns
        -------
        Dict[str, Any]
            检查结果
        """
        try:
            daily_loss_ratio = abs(daily_pnl) / portfolio_value if daily_pnl < 0 else 0

            if daily_loss_ratio > self.risk_limits.max_daily_loss:
                return {
                    "allowed": False,
                    "reason": f"Daily loss {daily_loss_ratio:.2%} exceeds limit {self.risk_limits.max_daily_loss:.2%}",
                    "loss_ratio": daily_loss_ratio,
                    "risk_level": RiskLevel.CRITICAL
                }

            return {
                "allowed": True,
                "loss_ratio": daily_loss_ratio,
                "risk_level": RiskLevel.LOW if daily_loss_ratio < self.risk_limits.max_daily_loss * 0.5 else RiskLevel.MEDIUM
            }

        except Exception as e:
            logger.error(f"Error checking daily loss: {e}")
            return {
                "allowed": False,
                "reason": f"Error in daily loss check: {str(e)}",
                "risk_level": RiskLevel.CRITICAL
            }

    def apply_stop_loss(self, positions: Dict[str, Position], current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """应用止损

        Parameters
        ----------
        positions: Dict[str, Position]
            当前持仓
        current_prices: Dict[str, float]
            当前价格

        Returns
        -------
        List[Dict[str, Any]]
            需要止损的订单列表
        """
        stop_loss_orders = []

        try:
            for symbol, position in positions.items():
                if symbol not in current_prices:
                    continue

                current_price = current_prices[symbol]
                price_change = (current_price - position.entry_price) / position.entry_price

                # 检查止损条件
                if price_change <= -self.risk_limits.stop_loss:
                    stop_loss_orders.append({
                        "symbol": symbol,
                        "action": "sell",
                        "amount": position.amount,
                        "price": current_price,
                        "reason": f"Stop loss triggered: {price_change:.2%}",
                        "risk_level": RiskLevel.HIGH
                    })

                    logger.warning(f"Stop loss triggered for {symbol}: {price_change:.2%}")

            return stop_loss_orders

        except Exception as e:
            logger.error(f"Error applying stop loss: {e}")
            return []

    def apply_trailing_stop(self, positions: Dict[str, Position], current_prices: Dict[str, float]) -> List[Dict[str, Any]]:
        """应用跟踪止损

        Parameters
        ----------
        positions: Dict[str, Position]
            当前持仓
        current_prices: Dict[str, float]
            当前价格

        Returns
        -------
        List[Dict[str, Any]]
            需要跟踪止损的订单列表
        """
        trailing_stop_orders = []

        try:
            for symbol, position in positions.items():
                if symbol not in current_prices:
                    continue

                current_price = current_prices[symbol]
                price_change = (current_price - position.entry_price) / position.entry_price

                # 计算跟踪止损价格
                if price_change > 0:  # 盈利状态
                    trailing_stop_price = current_price * (1 - self.risk_limits.trailing_stop)

                    # 检查是否触发跟踪止损
                    if trailing_stop_price > position.entry_price:
                        trailing_stop_orders.append({
                            "symbol": symbol,
                            "action": "sell",
                            "amount": position.amount,
                            "price": trailing_stop_price,
                            "reason": f"Trailing stop triggered: {price_change:.2%}",
                            "risk_level": RiskLevel.MEDIUM
                        })

            return trailing_stop_orders

        except Exception as e:
            logger.error(f"Error applying trailing stop: {e}")
            return []

    def check_liquidity(self, symbol: str, amount: float, price: float) -> Dict[str, Any]:
        """检查流动性

        Parameters
        ----------
        symbol: str
            交易对符号
        amount: float
            交易数量
        price: float
            交易价格

        Returns
        -------
        Dict[str, Any]
            检查结果
        """
        try:
            # 这里应该调用交易所 API 获取流动性信息
            # 为了简化，使用模拟数据
            estimated_slippage = self._estimate_slippage(symbol, amount, price)

            if estimated_slippage > self.risk_limits.max_slippage:
                return {
                    "allowed": False,
                    "reason": f"Estimated slippage {estimated_slippage:.2%} exceeds limit {self.risk_limits.max_slippage:.2%}",
                    "slippage": estimated_slippage,
                    "risk_level": RiskLevel.HIGH
                }

            return {
                "allowed": True,
                "slippage": estimated_slippage,
                "risk_level": RiskLevel.LOW
            }

        except Exception as e:
            logger.error(f"Error checking liquidity: {e}")
            return {
                "allowed": False,
                "reason": f"Error in liquidity check: {str(e)}",
                "risk_level": RiskLevel.CRITICAL
            }

    def calculate_risk_metrics(self, positions: Dict[str, Position], portfolio_value: float, price_history: pd.DataFrame = None) -> RiskMetrics:
        """计算风险指标

        Parameters
        ----------
        positions: Dict[str, Position]
            当前持仓
        portfolio_value: float
            组合价值
        price_history: pd.DataFrame
            价格历史数据

        Returns
        -------
        RiskMetrics
            风险指标
        """
        try:
            # 计算总敞口
            total_exposure = self._calculate_total_exposure(portfolio_value)

            # 计算回撤
            max_drawdown, current_drawdown = self._calculate_drawdown(portfolio_value)

            # 计算日/周收益
            daily_pnl = self._calculate_daily_pnl()
            weekly_pnl = self._calculate_weekly_pnl()

            # 计算夏普比率
            sharpe_ratio = self._calculate_sharpe_ratio()

            # 计算 VaR 和 CVaR
            var_95, cvar_95 = self._calculate_var_cvar()

            # 计算集中度风险
            concentration_risk = self._calculate_concentration_risk(positions, portfolio_value)

            # 计算相关性风险
            correlation_risk = self._calculate_correlation_risk(positions)

            return RiskMetrics(
                total_portfolio_value=portfolio_value,
                total_exposure=total_exposure,
                max_drawdown=max_drawdown,
                current_drawdown=current_drawdown,
                daily_pnl=daily_pnl,
                weekly_pnl=weekly_pnl,
                sharpe_ratio=sharpe_ratio,
                var_95=var_95,
                cvar_95=cvar_95,
                concentration_risk=concentration_risk,
                correlation_risk=correlation_risk
            )

        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            # 返回默认值
            return RiskMetrics(
                total_portfolio_value=portfolio_value,
                total_exposure=0.0,
                max_drawdown=0.0,
                current_drawdown=0.0,
                daily_pnl=0.0,
                weekly_pnl=0.0,
                sharpe_ratio=0.0,
                var_95=0.0,
                cvar_95=0.0,
                concentration_risk=0.0,
                correlation_risk=0.0
            )

    def generate_risk_report(self, risk_metrics: RiskMetrics) -> Dict[str, Any]:
        """生成风险报告

        Parameters
        ----------
        risk_metrics: RiskMetrics
            风险指标

        Returns
        -------
        Dict[str, Any]
            风险报告
        """
        try:
            # 评估风险等级
            overall_risk = self._assess_overall_risk(risk_metrics)

            # 生成建议
            recommendations = self._generate_recommendations(risk_metrics)

            # 生成告警
            alerts = self._generate_alerts(risk_metrics)

            report = {
                "timestamp": datetime.now().isoformat(),
                "overall_risk": overall_risk,
                "metrics": {
                    "total_portfolio_value": risk_metrics.total_portfolio_value,
                    "total_exposure": risk_metrics.total_exposure,
                    "max_drawdown": risk_metrics.max_drawdown,
                    "current_drawdown": risk_metrics.current_drawdown,
                    "daily_pnl": risk_metrics.daily_pnl,
                    "weekly_pnl": risk_metrics.weekly_pnl,
                    "sharpe_ratio": risk_metrics.sharpe_ratio,
                    "var_95": risk_metrics.var_95,
                    "cvar_95": risk_metrics.cvar_95,
                    "concentration_risk": risk_metrics.concentration_risk,
                    "correlation_risk": risk_metrics.correlation_risk
                },
                "recommendations": recommendations,
                "alerts": alerts
            }

            return report

        except Exception as e:
            logger.error(f"Error generating risk report: {e}")
            return {"error": str(e)}

    def _calculate_total_exposure(self, portfolio_value: float) -> float:
        """计算总敞口"""
        if not self.positions or portfolio_value <= 0:
            return 0.0

        total_exposure = sum(
            position.amount * position.current_price
            for position in self.positions.values()
        )

        return total_exposure / portfolio_value

    def _calculate_drawdown(self, current_value: float) -> Tuple[float, float]:
        """计算回撤"""
        if not self.portfolio_history:
            return 0.0, 0.0

        peak_value = max(self.portfolio_history)
        current_drawdown = (peak_value - current_value) / peak_value if peak_value > 0 else 0.0

        # 计算历史最大回撤
        max_drawdown = 0.0
        for i, value in enumerate(self.portfolio_history):
            peak = max(self.portfolio_history[:i+1])
            drawdown = (peak - value) / peak if peak > 0 else 0.0
            max_drawdown = max(max_drawdown, drawdown)

        return max_drawdown, current_drawdown

    def _calculate_daily_pnl(self) -> float:
        """计算日收益"""
        if len(self.daily_pnl_history) < 2:
            return 0.0

        return self.daily_pnl_history[-1] - self.daily_pnl_history[-2]

    def _calculate_weekly_pnl(self) -> float:
        """计算周收益"""
        if len(self.weekly_pnl_history) < 2:
            return 0.0

        return self.weekly_pnl_history[-1] - self.weekly_pnl_history[-2]

    def _calculate_sharpe_ratio(self) -> float:
        """计算夏普比率"""
        if len(self.daily_pnl_history) < 2:
            return 0.0

        returns = np.diff(self.daily_pnl_history)
        if len(returns) == 0 or np.std(returns) == 0:
            return 0.0

        return np.mean(returns) / np.std(returns) * np.sqrt(252)  # 年化

    def _calculate_var_cvar(self) -> Tuple[float, float]:
        """计算 VaR 和 CVaR"""
        if len(self.daily_pnl_history) < 2:
            return 0.0, 0.0

        returns = np.diff(self.daily_pnl_history)
        if len(returns) == 0:
            return 0.0, 0.0

        # 95% VaR
        var_95 = np.percentile(returns, 5)

        # 95% CVaR
        cvar_95 = np.mean(returns[returns <= var_95])

        return var_95, cvar_95

    def _calculate_concentration_risk(self, positions: Dict[str, Position], portfolio_value: float) -> float:
        """计算集中度风险"""
        if not positions or portfolio_value <= 0:
            return 0.0

        position_values = [
            position.amount * position.current_price
            for position in positions.values()
        ]

        if not position_values:
            return 0.0

        # 计算最大持仓占比
        max_position_ratio = max(position_values) / portfolio_value

        return max_position_ratio

    def _calculate_correlation_risk(self, positions: Dict[str, Position]) -> float:
        """计算相关性风险"""
        # 这里应该计算持仓之间的相关性
        # 为了简化，返回默认值
        return 0.0

    def _estimate_slippage(self, symbol: str, amount: float, price: float) -> float:
        """估算滑点"""
        # 这里应该基于订单簿深度估算滑点
        # 为了简化，使用固定值
        return 0.001  # 0.1%

    def _assess_overall_risk(self, risk_metrics: RiskMetrics) -> RiskLevel:
        """评估整体风险等级"""
        risk_score = 0

        # 回撤风险
        if risk_metrics.current_drawdown > self.risk_limits.max_drawdown * 0.8:
            risk_score += 3
        elif risk_metrics.current_drawdown > self.risk_limits.max_drawdown * 0.6:
            risk_score += 2
        elif risk_metrics.current_drawdown > self.risk_limits.max_drawdown * 0.4:
            risk_score += 1

        # 集中度风险
        if risk_metrics.concentration_risk > 0.4:
            risk_score += 2
        elif risk_metrics.concentration_risk > 0.3:
            risk_score += 1

        # 敞口风险
        if risk_metrics.total_exposure > self.risk_limits.max_total_exposure * 0.9:
            risk_score += 2
        elif risk_metrics.total_exposure > self.risk_limits.max_total_exposure * 0.7:
            risk_score += 1

        # 确定风险等级
        if risk_score >= 5:
            return RiskLevel.CRITICAL
        elif risk_score >= 3:
            return RiskLevel.HIGH
        elif risk_score >= 1:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(self, risk_metrics: RiskMetrics) -> List[str]:
        """生成风险建议"""
        recommendations = []

        if risk_metrics.current_drawdown > self.risk_limits.max_drawdown * 0.6:
            recommendations.append("考虑减少仓位以控制回撤")

        if risk_metrics.concentration_risk > 0.3:
            recommendations.append("考虑分散持仓以降低集中度风险")

        if risk_metrics.total_exposure > self.risk_limits.max_total_exposure * 0.8:
            recommendations.append("考虑降低总敞口")

        if risk_metrics.sharpe_ratio < 0.5:
            recommendations.append("考虑优化策略以提高风险调整后收益")

        return recommendations

    def _generate_alerts(self, risk_metrics: RiskMetrics) -> List[Dict[str, Any]]:
        """生成风险告警"""
        alerts = []

        if risk_metrics.current_drawdown > self.risk_limits.max_drawdown:
            alerts.append({
                "level": "CRITICAL",
                "message": f"回撤超过限制: {risk_metrics.current_drawdown:.2%}",
                "timestamp": datetime.now().isoformat()
            })

        if risk_metrics.concentration_risk > 0.4:
            alerts.append({
                "level": "HIGH",
                "message": f"集中度风险过高: {risk_metrics.concentration_risk:.2%}",
                "timestamp": datetime.now().isoformat()
            })

        if risk_metrics.total_exposure > self.risk_limits.max_total_exposure:
            alerts.append({
                "level": "HIGH",
                "message": f"总敞口超过限制: {risk_metrics.total_exposure:.2%}",
                "timestamp": datetime.now().isoformat()
            })

        return alerts

    def update_portfolio_value(self, value: float):
        """更新组合价值"""
        self.portfolio_history.append(value)

        # 保持历史记录长度
        if len(self.portfolio_history) > 1000:
            self.portfolio_history = self.portfolio_history[-1000:]

    def update_daily_pnl(self, pnl: float):
        """更新日收益"""
        self.daily_pnl_history.append(pnl)

        # 保持历史记录长度
        if len(self.daily_pnl_history) > 365:
            self.daily_pnl_history = self.daily_pnl_history[-365:]

    def update_weekly_pnl(self, pnl: float):
        """更新周收益"""
        self.weekly_pnl_history.append(pnl)

        # 保持历史记录长度
        if len(self.weekly_pnl_history) > 52:
            self.weekly_pnl_history = self.weekly_pnl_history[-52:]


def create_risk_manager(risk_limits: RiskLimits = None) -> RiskManager:
    """创建风险管理器

    Parameters
    ----------
    risk_limits: RiskLimits
        风险限制配置

    Returns
    -------
    RiskManager
        风险管理器实例
    """
    return RiskManager(risk_limits=risk_limits)


if __name__ == "__main__":
    # 测试风险管理器
    risk_manager = create_risk_manager()

    # 模拟持仓
    positions = {
        "BTCUSDT": Position(
            symbol="BTCUSDT",
            amount=0.1,
            entry_price=50000,
            current_price=48000,
            entry_time=datetime.now() - timedelta(days=1)
        )
    }

    # 计算风险指标
    risk_metrics = risk_manager.calculate_risk_metrics(positions, 100000)

    # 生成风险报告
    report = risk_manager.generate_risk_report(risk_metrics)

    print("Risk Report:")
    print(f"Overall Risk: {report['overall_risk']}")
    print(f"Current Drawdown: {report['metrics']['current_drawdown']:.2%}")
    print(f"Concentration Risk: {report['metrics']['concentration_risk']:.2%}")
    print(f"Recommendations: {report['recommendations']}")
    print(f"Alerts: {report['alerts']}")

