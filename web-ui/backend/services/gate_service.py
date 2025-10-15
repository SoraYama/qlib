#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate.io Trading Service - 封装 Gate.io 交易相关操作
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent.parent))

try:
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi
    GATE_API_AVAILABLE = True
except ImportError:
    GATE_API_AVAILABLE = False
    logger.warning("Gate.io API not available. Trading features will be disabled.")


class GateService:
    """Gate.io 交易服务封装类"""

    def __init__(self):
        """初始化 Gate.io 服务"""
        self.api_key = os.getenv("GATE_API_KEY")
        self.api_secret = os.getenv("GATE_API_SECRET")
        self.trading_enabled = False
        self.current_positions = {}
        self.trading_logs = []

        if GATE_API_AVAILABLE and self.api_key and self.api_secret:
            self._init_gate_api()

        logger.info("GateService initialized")

    def _init_gate_api(self):
        """初始化 Gate.io API"""
        try:
            config = Configuration(
                host="https://api.gateio.ws/api/v4",
                key=self.api_key,
                secret=self.api_secret
            )
            self.api_client = ApiClient(config)
            self.spot_api = SpotApi(self.api_client)
            self.trading_enabled = True
            logger.info("Gate.io API initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gate.io API: {e}")
            self.trading_enabled = False

    def get_trading_status(self) -> Dict[str, Any]:
        """获取交易状态"""
        return {
            "trading_enabled": self.trading_enabled,
            "api_available": GATE_API_AVAILABLE,
            "has_credentials": bool(self.api_key and self.api_secret),
            "current_positions": len(self.current_positions),
            "last_update": datetime.now().isoformat()
        }

    def start_trading(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """启动实盘交易"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled. Check API credentials."}

            # 这里应该实现启动交易策略的逻辑
            # 包括加载模型、设置风险参数、启动定时任务等

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Trading started with config: {config}"
            })

            return {
                "success": True,
                "message": "Trading started successfully",
                "config": config
            }

        except Exception as e:
            logger.error(f"Error starting trading: {e}")
            return {"error": str(e)}

    def stop_trading(self) -> Dict[str, Any]:
        """停止实盘交易"""
        try:
            # 这里应该实现停止交易策略的逻辑
            # 包括平仓、停止定时任务等

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": "Trading stopped"
            })

            return {
                "success": True,
                "message": "Trading stopped successfully"
            }

        except Exception as e:
            logger.error(f"Error stopping trading: {e}")
            return {"error": str(e)}

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        try:
            if not self.trading_enabled:
                return []

            # 调用 Gate.io API 获取账户信息
            accounts = self.spot_api.list_spot_accounts()

            positions = []
            for account in accounts:
                if float(account.available) > 0 or float(account.locked) > 0:
                    positions.append({
                        "currency": account.currency,
                        "available": float(account.available),
                        "locked": float(account.locked),
                        "total": float(account.available) + float(account.locked)
                    })

            self.current_positions = {pos["currency"]: pos for pos in positions}
            return positions

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取订单历史"""
        try:
            if not self.trading_enabled:
                return []

            # 调用 Gate.io API 获取订单历史
            orders = self.spot_api.list_orders(limit=limit, offset=offset)

            order_list = []
            for order in orders:
                order_list.append({
                    "id": order.id,
                    "currency_pair": order.currency_pair,
                    "side": order.side,
                    "amount": float(order.amount),
                    "price": float(order.price) if order.price else None,
                    "status": order.status,
                    "create_time": order.create_time,
                    "update_time": order.update_time
                })

            return order_list

        except Exception as e:
            logger.error(f"Error getting orders: {e}")
            return []

    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            # 调用 Gate.io API 获取账户信息
            accounts = self.spot_api.list_spot_accounts()

            total_balance = 0.0
            account_info = {
                "currencies": [],
                "total_balance": 0.0,
                "last_update": datetime.now().isoformat()
            }

            for account in accounts:
                balance = float(account.available) + float(account.locked)
                if balance > 0:
                    account_info["currencies"].append({
                        "currency": account.currency,
                        "available": float(account.available),
                        "locked": float(account.locked),
                        "total": balance
                    })
                    total_balance += balance

            account_info["total_balance"] = total_balance
            return account_info

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}

    def get_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        try:
            if not self.trading_enabled:
                return {}

            accounts = self.spot_api.list_spot_accounts()
            balance = {}

            for account in accounts:
                total = float(account.available) + float(account.locked)
                if total > 0:
                    balance[account.currency] = total

            return balance

        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {}

    def get_risk_metrics(self) -> Dict[str, Any]:
        """获取风险指标"""
        try:
            # 计算风险指标
            positions = self.get_positions()
            total_value = sum(pos["total"] for pos in positions)

            risk_metrics = {
                "total_portfolio_value": total_value,
                "position_count": len(positions),
                "max_single_position": max((pos["total"] for pos in positions), default=0),
                "concentration_risk": 0.0,
                "last_update": datetime.now().isoformat()
            }

            if total_value > 0:
                risk_metrics["concentration_risk"] = risk_metrics["max_single_position"] / total_value

            return risk_metrics

        except Exception as e:
            logger.error(f"Error getting risk metrics: {e}")
            return {"error": str(e)}

    def update_risk_settings(self, risk_settings: Dict[str, Any]) -> Dict[str, Any]:
        """更新风险设置"""
        try:
            # 这里应该实现更新风险设置的逻辑
            # 包括最大仓位、止损线、最大回撤等

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Risk settings updated: {risk_settings}"
            })

            return {
                "success": True,
                "message": "Risk settings updated successfully",
                "settings": risk_settings
            }

        except Exception as e:
            logger.error(f"Error updating risk settings: {e}")
            return {"error": str(e)}

    def get_trading_performance(self) -> Dict[str, Any]:
        """获取交易表现"""
        try:
            # 这里应该实现计算交易表现的逻辑
            # 包括收益率、夏普比率、最大回撤等

            performance = {
                "total_return": 0.0,
                "daily_return": 0.0,
                "sharpe_ratio": 0.0,
                "max_drawdown": 0.0,
                "win_rate": 0.0,
                "total_trades": 0,
                "last_update": datetime.now().isoformat()
            }

            return performance

        except Exception as e:
            logger.error(f"Error getting trading performance: {e}")
            return {"error": str(e)}

    def get_trading_logs(self, limit: int = 100, level: str = "INFO") -> List[Dict[str, Any]]:
        """获取交易日志"""
        try:
            # 过滤日志级别
            filtered_logs = [
                log for log in self.trading_logs
                if log["level"] == level or level == "ALL"
            ]

            # 限制数量
            return filtered_logs[-limit:] if limit > 0 else filtered_logs

        except Exception as e:
            logger.error(f"Error getting trading logs: {e}")
            return []

    def place_order(
        self,
        currency_pair: str,
        side: str,
        amount: float,
        price: float = None,
        order_type: str = "limit"
    ) -> Dict[str, Any]:
        """下单"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            # 调用 Gate.io API 下单
            order = self.spot_api.create_order(
                currency_pair=currency_pair,
                side=side,
                amount=str(amount),
                price=str(price) if price else None,
                type=order_type
            )

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Order placed: {order.id} - {side} {amount} {currency_pair} at {price}"
            })

            return {
                "success": True,
                "order_id": order.id,
                "status": order.status,
                "message": "Order placed successfully"
            }

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "ERROR",
                "message": f"Order failed: {str(e)}"
            })
            return {"error": str(e)}

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            # 调用 Gate.io API 取消订单
            self.spot_api.cancel_order(order_id)

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Order cancelled: {order_id}"
            })

            return {
                "success": True,
                "message": f"Order {order_id} cancelled successfully"
            }

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}

