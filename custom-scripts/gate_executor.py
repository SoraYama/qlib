#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate.io Trading Executor for Qlib
Implements real trading execution on Gate.io exchange
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

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

try:
    import gate_api
    from gate_api import ApiClient, Configuration, SpotApi
    GATE_API_AVAILABLE = True
except ImportError:
    GATE_API_AVAILABLE = False
    logger.warning("Gate.io API not available. Trading features will be disabled.")

try:
    from qlib.backtest.executor import BaseExecutor
    from qlib.backtest.order import Order
    from qlib.backtest.position import Position
    QLIB_AVAILABLE = True
except ImportError:
    QLIB_AVAILABLE = False
    logger.warning("Qlib not available. Some features will be disabled.")


class GateExecutor(BaseExecutor):
    """Gate.io 实盘交易执行器"""

    def __init__(
        self,
        api_key: str = None,
        api_secret: str = None,
        sandbox: bool = False,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        **kwargs
    ):
        """
        初始化 Gate.io 交易执行器

        Parameters
        ----------
        api_key: str
            Gate.io API Key
        api_secret: str
            Gate.io API Secret
        sandbox: bool
            是否使用沙盒环境
        max_retries: int
            最大重试次数
        retry_delay: float
            重试延迟（秒）
        **kwargs: dict
            其他参数
        """
        super().__init__(**kwargs)

        # API 配置
        self.api_key = api_key or os.getenv("GATE_API_KEY")
        self.api_secret = api_secret or os.getenv("GATE_API_SECRET")
        self.sandbox = sandbox
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        # 交易状态
        self.trading_enabled = False
        self.orders = {}  # 订单记录
        self.positions = {}  # 持仓记录
        self.balance = {}  # 余额记录

        # 初始化 API
        if GATE_API_AVAILABLE and self.api_key and self.api_secret:
            self._init_gate_api()

        logger.info("GateExecutor initialized")

    def _init_gate_api(self):
        """初始化 Gate.io API"""
        try:
            # 选择环境
            if self.sandbox:
                host = "https://fx-api-testnet.gateio.ws/api/v4"
            else:
                host = "https://api.gateio.ws/api/v4"

            config = Configuration(
                host=host,
                key=self.api_key,
                secret=self.api_secret
            )

            self.api_client = ApiClient(config)
            self.spot_api = SpotApi(self.api_client)
            self.trading_enabled = True

            logger.info(f"Gate.io API initialized (sandbox: {self.sandbox})")

        except Exception as e:
            logger.error(f"Error initializing Gate.io API: {e}")
            self.trading_enabled = False

    def execute_order(self, order: Order) -> Dict[str, Any]:
        """执行订单

        Parameters
        ----------
        order: Order
            Qlib 订单对象

        Returns
        -------
        Dict[str, Any]
            执行结果
        """
        if not self.trading_enabled:
            return {
                "success": False,
                "error": "Trading not enabled. Check API credentials."
            }

        try:
            # 1. 订单前检查
            pre_check_result = self._pre_order_check(order)
            if not pre_check_result["success"]:
                return pre_check_result

            # 2. 转换订单格式
            gate_order = self._convert_order_to_gate(order)

            # 3. 执行订单
            execution_result = self._execute_gate_order(gate_order)

            # 4. 记录订单
            if execution_result["success"]:
                self._record_order(order, execution_result)

            return execution_result

        except Exception as e:
            logger.error(f"Error executing order: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    def _pre_order_check(self, order: Order) -> Dict[str, Any]:
        """订单前检查"""
        try:
            # 检查余额
            balance = self.get_balance()
            currency_pair = self._get_currency_pair(order.stock_id)
            base_currency, quote_currency = currency_pair.split("_")

            if order.direction == Order.BUY:
                # 买入：检查 USDT 余额
                required_amount = order.amount * order.price
                available_balance = balance.get(quote_currency, 0)

                if available_balance < required_amount:
                    return {
                        "success": False,
                        "error": f"Insufficient {quote_currency} balance. Required: {required_amount}, Available: {available_balance}"
                    }
            else:
                # 卖出：检查币种余额
                available_balance = balance.get(base_currency, 0)

                if available_balance < order.amount:
                    return {
                        "success": False,
                        "error": f"Insufficient {base_currency} balance. Required: {order.amount}, Available: {available_balance}"
                    }

            # 检查最小下单量
            min_amount = self._get_min_order_amount(currency_pair)
            if order.amount < min_amount:
                return {
                    "success": False,
                    "error": f"Order amount {order.amount} below minimum {min_amount}"
                }

            return {"success": True}

        except Exception as e:
            logger.error(f"Error in pre-order check: {e}")
            return {"success": False, "error": str(e)}

    def _convert_order_to_gate(self, order: Order) -> Dict[str, Any]:
        """转换 Qlib 订单为 Gate.io 格式"""
        currency_pair = self._get_currency_pair(order.stock_id)

        gate_order = {
            "currency_pair": currency_pair,
            "side": "buy" if order.direction == Order.BUY else "sell",
            "amount": str(order.amount),
            "price": str(order.price) if order.price else None,
            "type": "limit" if order.price else "market"
        }

        return gate_order

    def _execute_gate_order(self, gate_order: Dict[str, Any]) -> Dict[str, Any]:
        """执行 Gate.io 订单"""
        for attempt in range(self.max_retries):
            try:
                # 调用 Gate.io API 下单
                order = self.spot_api.create_order(
                    currency_pair=gate_order["currency_pair"],
                    side=gate_order["side"],
                    amount=gate_order["amount"],
                    price=gate_order.get("price"),
                    type=gate_order["type"]
                )

                logger.info(f"Order placed successfully: {order.id}")

                return {
                    "success": True,
                    "order_id": order.id,
                    "status": order.status,
                    "gate_order": order
                }

            except Exception as e:
                logger.warning(f"Order attempt {attempt + 1} failed: {e}")

                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                else:
                    return {
                        "success": False,
                        "error": f"Order failed after {self.max_retries} attempts: {str(e)}"
                    }

    def _record_order(self, order: Order, execution_result: Dict[str, Any]):
        """记录订单"""
        order_record = {
            "order_id": execution_result["order_id"],
            "stock_id": order.stock_id,
            "direction": order.direction,
            "amount": order.amount,
            "price": order.price,
            "status": execution_result["status"],
            "timestamp": datetime.now().isoformat(),
            "gate_order": execution_result.get("gate_order")
        }

        self.orders[execution_result["order_id"]] = order_record
        logger.info(f"Order recorded: {execution_result['order_id']}")

    def _get_currency_pair(self, stock_id: str) -> str:
        """获取交易对格式"""
        # 将 BTCUSDT 转换为 BTC_USDT
        if stock_id.endswith("USDT"):
            base = stock_id[:-4]
            return f"{base}_USDT"
        else:
            return stock_id

    def _get_min_order_amount(self, currency_pair: str) -> float:
        """获取最小下单量"""
        # 这里应该调用 Gate.io API 获取交易对信息
        # 为了简化，使用默认值
        min_amounts = {
            "BTC_USDT": 0.001,
            "ETH_USDT": 0.01,
        }
        return min_amounts.get(currency_pair, 0.01)

    def get_account_info(self) -> Dict[str, Any]:
        """获取账户信息"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            accounts = self.spot_api.list_spot_accounts()

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
                    account_info["total_balance"] += balance

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

            self.balance = balance
            return balance

        except Exception as e:
            logger.error(f"Error getting balance: {e}")
            return {}

    def get_positions(self) -> List[Dict[str, Any]]:
        """获取当前持仓"""
        try:
            if not self.trading_enabled:
                return []

            accounts = self.spot_api.list_spot_accounts()
            positions = []

            for account in accounts:
                if float(account.available) > 0 or float(account.locked) > 0:
                    position = {
                        "currency": account.currency,
                        "available": float(account.available),
                        "locked": float(account.locked),
                        "total": float(account.available) + float(account.locked)
                    }
                    positions.append(position)
                    self.positions[account.currency] = position

            return positions

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """获取订单历史"""
        try:
            if not self.trading_enabled:
                return []

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

    def cancel_order(self, order_id: str) -> Dict[str, Any]:
        """取消订单"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            self.spot_api.cancel_order(order_id)

            # 更新本地记录
            if order_id in self.orders:
                self.orders[order_id]["status"] = "cancelled"

            logger.info(f"Order cancelled: {order_id}")

            return {
                "success": True,
                "message": f"Order {order_id} cancelled successfully"
            }

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}

    def get_order_status(self, order_id: str) -> Dict[str, Any]:
        """获取订单状态"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            order = self.spot_api.get_order(order_id)

            return {
                "order_id": order.id,
                "status": order.status,
                "amount": float(order.amount),
                "price": float(order.price) if order.price else None,
                "filled_amount": float(order.filled_total),
                "create_time": order.create_time,
                "update_time": order.update_time
            }

        except Exception as e:
            logger.error(f"Error getting order status: {e}")
            return {"error": str(e)}

    def get_trading_fees(self) -> Dict[str, float]:
        """获取交易手续费"""
        try:
            if not self.trading_enabled:
                return {}

            # 这里应该调用 Gate.io API 获取手续费信息
            # 为了简化，使用默认值
            return {
                "maker": 0.002,  # 0.2%
                "taker": 0.002   # 0.2%
            }

        except Exception as e:
            logger.error(f"Error getting trading fees: {e}")
            return {}

    def get_market_data(self, currency_pair: str) -> Dict[str, Any]:
        """获取市场数据"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled"}

            # 获取最新价格
            ticker = self.spot_api.get_ticker(currency_pair)

            return {
                "currency_pair": currency_pair,
                "last_price": float(ticker.last),
                "bid_price": float(ticker.highest_bid),
                "ask_price": float(ticker.lowest_ask),
                "volume": float(ticker.quote_volume),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Error getting market data: {e}")
            return {"error": str(e)}

    def get_trading_status(self) -> Dict[str, Any]:
        """获取交易状态"""
        return {
            "trading_enabled": self.trading_enabled,
            "api_available": GATE_API_AVAILABLE,
            "has_credentials": bool(self.api_key and self.api_secret),
            "sandbox": self.sandbox,
            "total_orders": len(self.orders),
            "total_positions": len(self.positions),
            "last_update": datetime.now().isoformat()
        }


def create_gate_executor(
    api_key: str = None,
    api_secret: str = None,
    sandbox: bool = False,
    **kwargs
) -> GateExecutor:
    """创建 Gate.io 交易执行器

    Parameters
    ----------
    api_key: str
        Gate.io API Key
    api_secret: str
        Gate.io API Secret
    sandbox: bool
        是否使用沙盒环境
    **kwargs: dict
        其他参数

    Returns
    -------
    GateExecutor
        交易执行器实例
    """
    return GateExecutor(
        api_key=api_key,
        api_secret=api_secret,
        sandbox=sandbox,
        **kwargs
    )


if __name__ == "__main__":
    # 测试交易执行器
    executor = create_gate_executor(sandbox=True)

    # 获取交易状态
    status = executor.get_trading_status()
    print(f"Trading Status: {status}")

    # 获取账户信息
    account_info = executor.get_account_info()
    print(f"Account Info: {account_info}")

    # 获取余额
    balance = executor.get_balance()
    print(f"Balance: {balance}")

    # 获取持仓
    positions = executor.get_positions()
    print(f"Positions: {positions}")

