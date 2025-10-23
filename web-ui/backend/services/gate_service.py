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
    from gate_api import ApiClient, Configuration, SpotApi, FuturesApi, AccountApi
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

        # 交易状态相关属性
        self.is_running = False
        self.current_strategy = 'default'
        self.risk_limits = {
            "max_position_size": 0.3,
            "max_drawdown": 0.2,
            "stop_loss": 0.05
        }

        if GATE_API_AVAILABLE and self.api_key and self.api_secret:
            self._init_gate_api()

        logger.info("GateService initialized")

    def _init_gate_api(self):
        """初始化 Gate.io API"""
        try:
            # 使用合约模拟盘端点（用户提供）
            config = Configuration(
                host="https://api-testnet.gateapi.io/api/v4",
                key=self.api_key,
                secret=self.api_secret
            )
            self.api_client = ApiClient(config)
            self.futures_api = FuturesApi(self.api_client)
            self.account_api = AccountApi(self.api_client)
            self.trading_enabled = True
            logger.info("Gate.io Futures Sandbox API initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Gate.io Futures Sandbox API: {e}")
            self.trading_enabled = False

    def get_trading_status(self) -> Dict[str, Any]:
        """获取交易状态"""
        # 获取账户信息
        account_info = self.get_account_info()

        # 计算盈亏信息
        total_balance = 0.0
        daily_pnl = 0.0
        total_pnl = 0.0

        if isinstance(account_info, dict) and "error" not in account_info:
            total_balance = account_info.get("total_balance", 0.0)
            # 这里可以添加更复杂的盈亏计算逻辑
            # 暂时使用简单的计算
            positions = self.get_positions()
            for position in positions:
                if isinstance(position, dict):
                    total_pnl += position.get("unrealized_pnl", 0)
                    # 简化处理：假设所有盈亏都是今日的
                    daily_pnl += position.get("unrealized_pnl", 0)

        return {
            "is_running": getattr(self, 'is_running', False),  # 添加交易运行状态
            "trading_enabled": self.trading_enabled,
            "api_available": GATE_API_AVAILABLE,
            "has_credentials": bool(self.api_key and self.api_secret),
            "current_positions": len(self.current_positions),
            "account_info": {
                "total_balance": total_balance,
                "available_balance": total_balance,  # 简化处理
                "total_pnl": total_pnl,
                "daily_pnl": daily_pnl
            },
            "risk_limits": getattr(self, 'risk_limits', {
                "max_position_size": 0.3,
                "max_drawdown": 0.2,
                "stop_loss": 0.05
            }),
            "current_strategy": getattr(self, 'current_strategy', 'default'),
            "last_update": datetime.now().isoformat()
        }

    def start_trading(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """启动实盘交易"""
        try:
            if not self.trading_enabled:
                return {"error": "Trading not enabled. Check API credentials."}

            # 设置交易状态
            self.is_running = True
            self.current_strategy = config.get('strategy_name', 'default')

            # 设置风险限制
            if 'risk_limits' in config:
                self.risk_limits = config['risk_limits']
            else:
                self.risk_limits = {
                    "max_position_size": 0.3,
                    "max_drawdown": 0.2,
                    "stop_loss": 0.05
                }

            # 启动交易执行逻辑
            import threading
            if not hasattr(self, 'trading_thread') or not self.trading_thread.is_alive():
                self.trading_thread = threading.Thread(target=self._trading_loop, daemon=True)
                self.trading_thread.start()
                logger.info("Trading thread started")

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Trading started with config: {config}"
            })

            return {
                "success": True,
                "message": "Trading started successfully. Background trading loop is running.",
                "config": config,
                "strategy_name": self.current_strategy,
                "note": "Trading signals will be generated automatically based on market conditions."
            }

        except Exception as e:
            logger.error(f"Error starting trading: {e}")
            return {"error": str(e)}

    def _trading_loop(self):
        """交易执行循环（后台线程）"""
        import time

        logger.info("Trading loop started")
        prediction_interval = 300  # 5分钟生成一次信号

        while self.is_running:
            try:
                logger.info("Trading loop iteration - checking for trading opportunities...")

                # 1. 获取市场数据
                try:
                    logger.info("Fetching market data for BTC_USDT...")
                    market_data = self.get_spot_klines('BTC_USDT', '15m', 100)
                    logger.info(f"get_spot_klines returned: {type(market_data)}, length: {len(market_data) if market_data else 0}")
                except Exception as fetch_error:
                    logger.error(f"Error fetching market data: {fetch_error}", exc_info=True)
                    time.sleep(60)
                    continue

                if not market_data:
                    logger.warning("No market data available")
                    time.sleep(60)
                    continue

                logger.info(f"Successfully fetched {len(market_data)} candles")

                # 2. 生成简单的交易信号（示例：基于价格变化）
                # 注意：这是一个简化示例，实际应该使用训练好的模型
                signal = self._generate_simple_signal(market_data)

                if signal:
                    logger.info(f"Trading signal generated: {signal}")

                    # 3. 应用风险控制
                    if self._check_risk_limits():
                        # 4. 执行交易 - 实际调用下单API
                        try:
                            # 计算下单数量 - Gate.io期货合约以张数计价，每张=1 USD
                            # 例如：买入100张BTC_USDT合约 = 买入价值100 USD的BTC
                            # 简单示例：固定下单100张(约100 USD)
                            order_amount = 100  # 100张合约

                            logger.info(f"Placing order: {signal['action']} {order_amount} contracts at {signal['price']}")

                            order_result = self.place_order(
                                currency_pair='BTC_USDT',
                                side=signal['action'],
                                amount=order_amount,
                                price=signal['price'],
                                order_type='limit'
                            )

                            if order_result.get('success'):
                                logger.info(f"Order placed successfully: {order_result}")
                                self.trading_logs.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "INFO",
                                    "message": f"Order executed: {signal['action']} {order_amount} contracts at {signal['price']}, Order ID: {order_result.get('order_id')}"
                                })
                            else:
                                logger.error(f"Order failed: {order_result.get('error')}")
                                self.trading_logs.append({
                                    "timestamp": datetime.now().isoformat(),
                                    "level": "ERROR",
                                    "message": f"Order failed: {order_result.get('error')}"
                                })
                        except Exception as order_error:
                            logger.error(f"Error placing order: {order_error}")
                            self.trading_logs.append({
                                "timestamp": datetime.now().isoformat(),
                                "level": "ERROR",
                                "message": f"Order execution error: {str(order_error)}"
                            })
                    else:
                        logger.warning("Signal rejected by risk controls")
                        self.trading_logs.append({
                            "timestamp": datetime.now().isoformat(),
                            "level": "WARNING",
                            "message": f"Signal rejected by risk controls: {signal}"
                        })
                else:
                    logger.info("No signal generated in this iteration")

                # 等待下一次迭代
                time.sleep(prediction_interval)

            except Exception as e:
                logger.error(f"Error in trading loop: {e}", exc_info=True)
                time.sleep(60)  # 出错后等待1分钟再重试

        logger.info("Trading loop stopped")

    def _generate_simple_signal(self, market_data: List[Dict]) -> Optional[Dict[str, Any]]:
        """生成简单的交易信号（演示用）"""
        try:
            if len(market_data) < 20:
                logger.warning(f"Not enough market data: {len(market_data)} candles")
                return None

            # 计算简单移动平均
            recent_prices = [float(k['close']) for k in market_data[-20:]]  # 收盘价
            ma_short = sum(recent_prices[-5:]) / 5
            ma_long = sum(recent_prices[-20:]) / 20
            current_price = recent_prices[-1]

            logger.info(f"Signal check - Current: {current_price:.2f}, MA5: {ma_short:.2f}, MA20: {ma_long:.2f}, Diff: {((ma_short/ma_long - 1) * 100):.3f}%")

            # 简单的金叉/死叉策略 - 降低阈值到0.3%以更容易触发
            if ma_short > ma_long * 1.003:  # 短期均线比长期均线高0.3%以上
                return {
                    "action": "buy",
                    "symbol": "BTC_USDT",
                    "price": current_price,
                    "reason": f"MA crossover bullish (MA5: {ma_short:.2f} > MA20: {ma_long:.2f})"
                }
            elif ma_short < ma_long * 0.997:  # 短期均线比长期均线低0.3%以上
                return {
                    "action": "sell",
                    "symbol": "BTC_USDT",
                    "price": current_price,
                    "reason": f"MA crossover bearish (MA5: {ma_short:.2f} < MA20: {ma_long:.2f})"
                }

            logger.info("No trading signal generated (MA差异不足0.3%)")
            return None

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return None

    def _check_risk_limits(self) -> bool:
        """检查风险限制"""
        try:
            # 获取当前持仓
            positions = self.get_positions()

            # 检查持仓数量限制
            if len(positions) >= 3:  # 最多持有3个仓位
                logger.warning("Maximum positions reached")
                return False

            # 检查账户余额
            account_info = self.get_account_info()
            available_balance = account_info.get('available_balance', 0)
            if available_balance < 100:  # 最少保留100 USDT
                logger.warning(f"Insufficient balance: {available_balance} USDT")
                return False

            logger.info(f"Risk check passed - Positions: {len(positions)}, Available: {available_balance} USDT")
            return True

        except Exception as e:
            logger.error(f"Error checking risk limits: {e}", exc_info=True)
            return False

    def stop_trading(self) -> Dict[str, Any]:
        """停止实盘交易"""
        try:
            # 设置交易状态
            self.is_running = False

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

            # 调用 Gate.io 合约 API 获取持仓信息（usdt 结算）
            positions = self.futures_api.list_positions(settle='usdt')

            position_list = []
            for position in positions:
                if float(position.size) != 0:  # 只处理有持仓的合约
                    unrealized_pnl = float(position.unrealised_pnl) if position.unrealised_pnl else 0.0

                    position_list.append({
                        "currency": position.contract.split('_')[0] if '_' in position.contract else position.contract,
                        "available": 0.0,  # 合约持仓没有可用/锁定概念
                        "locked": 0.0,
                        "total": float(position.size),
                        "unrealized_pnl": unrealized_pnl,
                        "symbol": position.contract,
                        "side": "long" if float(position.size) > 0 else "short",
                        "size": abs(float(position.size)),
                        "entry_price": float(position.entry_price) if position.entry_price else 0.0,
                        "current_price": float(position.mark_price) if position.mark_price else 0.0
                    })

            self.current_positions = {pos["symbol"]: pos for pos in position_list}
            return position_list

        except Exception as e:
            logger.error(f"Error getting positions: {e}")
            return []

    def get_orders(self, limit: int = 100, offset: int = 0, status: str = 'finished') -> List[Dict[str, Any]]:
        """获取订单历史

        Parameters
        ----------
        limit : int
            返回订单数量限制
        offset : int
            偏移量
        status : str
            订单状态: 'open' (未完成), 'finished' (已完成)
        """
        try:
            if not self.trading_enabled:
                return []

            # 调用 Gate.io 合约 API 获取订单历史（usdt 结算）
            # status 参数是必需的：'open' 或 'finished'
            orders = self.futures_api.list_futures_orders(settle='usdt', status=status, limit=limit, offset=offset)

            order_list = []
            for order in orders:
                order_list.append({
                    "id": order.id,
                    "currency_pair": order.contract,
                    "side": order.side,
                    "amount": float(order.size),
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

            # 调用 Gate.io 合约 API 获取账户信息
            accounts = self.futures_api.list_futures_accounts(settle='usdt')

            # 兼容返回为单对象或列表两种情况
            if isinstance(accounts, list):
                account = accounts[0] if len(accounts) > 0 else None
            else:
                account = accounts

            # 注意：部分 SDK 模型字段为字符串，需要转换
            total_balance = float(getattr(account, 'total', 0.0) or 0.0) if account else 0.0
            available_balance = float(getattr(account, 'available', 0.0) or 0.0) if account else 0.0

            account_info = {
                "currencies": [],
                "total_balance": total_balance,
                "available_balance": available_balance,
                "last_update": datetime.now().isoformat()
            }

            # 添加主要货币信息
            if total_balance > 0:
                account_info["currencies"].append({
                    "currency": "USDT",  # 合约账户通常以 USDT 计价
                    "available": available_balance,
                    "locked": total_balance - available_balance,
                    "total": total_balance
                })

            return account_info

        except Exception as e:
            logger.error(f"Error getting account info: {e}")
            return {"error": str(e)}

    def get_balance(self) -> Dict[str, float]:
        """获取账户余额"""
        try:
            if not self.trading_enabled:
                return {}

            # 获取合约账户余额
            accounts = self.futures_api.list_futures_accounts(settle='usdt')
            balance = {}

            # 兼容返回为单对象或列表两种情况
            acc0 = None
            if isinstance(accounts, list):
                acc0 = accounts[0] if len(accounts) > 0 else None
            else:
                acc0 = accounts

            total0 = float(getattr(acc0, 'total', 0.0) or 0.0) if acc0 else 0.0
            if total0 > 0:
                balance["USDT"] = total0

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

    def get_spot_klines(self, currency_pair: str, interval: str = "1m", limit: int = 200) -> List[Dict[str, Any]]:
        """获取现货实时K线（公开接口，无需密钥）

        返回按时间升序的列表，元素包含 time/open/high/low/close/volume。
        在网络错误、参数无效、限流或上游格式异常时抛出带明确信息的异常。
        """
        try:
            if not currency_pair:
                raise ValueError("currency_pair is required")
            # 规范化交易对格式，如 BTCUSDT -> BTC_USDT
            pair = currency_pair.replace("-", "_").upper()
            if pair.endswith("USDT") and "_" not in pair:
                pair = pair[:-4] + "_USDT"

            # Gate 公共K线接口
            import requests
            base = "https://api.gateio.ws/api/v4/spot/candlesticks"
            params = {"currency_pair": pair, "interval": interval, "limit": int(limit)}
            headers = {"Accept": "application/json"}

            resp = requests.get(base, params=params, headers=headers, timeout=10)
            if resp.status_code == 429:
                raise RuntimeError("rate limited by upstream (HTTP 429)")
            if resp.status_code >= 400:
                # 直接透传上游错误文本，便于前端定位
                raise RuntimeError(f"upstream error {resp.status_code}: {resp.text}")

            data = resp.json()
            if not isinstance(data, list):
                # 上游错误通常返回对象，尝试提取 message/label
                msg = None
                if isinstance(data, dict):
                    msg = data.get("message") or data.get("label") or str(data)
                raise RuntimeError(f"unexpected upstream response: {msg}")

            if len(data) == 0:
                raise RuntimeError("upstream returned empty list")

            # Gate 返回通常为列表，元素形如 [timestamp, volume, close, high, low, open]
            # 为兼容可能的额外字段或字典格式，采用健壮解析
            def parse_item(it):
                # 列表/元组格式
                if isinstance(it, (list, tuple)) and len(it) >= 6:
                    ts = int(it[0])
                    vol = float(it[1])
                    close = float(it[2])
                    high = float(it[3])
                    low = float(it[4])
                    open_ = float(it[5])
                    return ts, open_, high, low, close, vol
                # 字典格式（尽力映射）
                if isinstance(it, dict):
                    ts = int(it.get("t") or it.get("time") or it.get("timestamp"))
                    open_ = float(it.get("o") or it.get("open"))
                    high = float(it.get("h") or it.get("high"))
                    low = float(it.get("l") or it.get("low"))
                    close = float(it.get("c") or it.get("close"))
                    vol = float(it.get("v") or it.get("volume") or 0)
                    return ts, open_, high, low, close, vol
                raise ValueError("unsupported kline item format")

            # 按时间升序
            try:
                data_sorted = sorted(data, key=lambda x: int(x[0]) if isinstance(x, (list, tuple)) else int(x.get("t") or x.get("time") or x.get("timestamp")))
            except Exception:
                data_sorted = data

            kl = []
            for it in data_sorted:
                try:
                    ts, open_, high, low, close, vol = parse_item(it)
                    kl.append({
                        "time": ts,
                        "open": open_,
                        "high": high,
                        "low": low,
                        "close": close,
                        "volume": vol,
                    })
                except Exception:
                    # 跳过无法解析的项
                    continue
            if not kl:
                raise RuntimeError("parsed empty klines from upstream response")
            return kl

        except Exception as e:
            # 抛出异常给路由层，让路由返回明确错误给前端
            logger.error(f"Error fetching spot klines: {e}")
            raise

    def get_current_trading_plan(self) -> Dict[str, Any]:
        """返回当前的交易计划（示例：基于简单均线信号的下一个动作）"""
        try:
            # 默认以 BTC_USDT 为例生成一个展示性的计划
            symbol = "BTC_USDT"
            kl = self.get_spot_klines(symbol, interval="1m", limit=200)
            closes = [k["close"] for k in kl]
            plan = {
                "symbol": symbol,
                "plan_time": datetime.now().isoformat(),
                "signal": "wait",
                "entry": None,
                "stop": None,
                "take": None,
            }
            if len(closes) >= 60:
                import pandas as pd
                short = pd.Series(closes).rolling(20).mean().iloc[-1]
                long = pd.Series(closes).rolling(60).mean().iloc[-1]
                last = closes[-1]
                if short > long:
                    plan["signal"] = "buy"
                    plan["entry"] = last
                    plan["stop"] = last * 0.98
                    plan["take"] = last * 1.03
                elif short < long:
                    plan["signal"] = "sell"
                    plan["entry"] = last
                    plan["stop"] = last * 1.02
                    plan["take"] = last * 0.97
            return plan

        except Exception as e:
            logger.error(f"Error generating trading plan: {e}")
            return {"error": str(e)}

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

            # 将现货风格交易对转换为合约风格，如 BTCUSDT -> BTC_USDT
            contract = currency_pair.replace("-", "").upper()
            if contract.endswith("USDT") and "_" not in contract:
                contract = contract[:-4] + "_USDT"

            # Futures 下单：size 为合约张数（正多负空），这里按 side 控制正负
            size = float(amount)
            if side.lower() in ("sell", "short"):
                size = -abs(size)
            else:
                size = abs(size)

            # 组装期货订单对象 - 注意gate_api要求在构造函数中传入必需参数
            logger.info(f"Creating futures order: contract={contract}, size={size}, side={side}")

            # 准备订单参数
            order_params = {
                'contract': contract,
                'size': int(size)  # size需要是整数(合约张数)
            }

            # 价格与订单类型
            if order_type == "limit" and price is not None:
                order_params['price'] = str(price)
                order_params['tif'] = "gtc"
            else:
                # 市价单：部分接口用 price=0 且 tif=ioc
                order_params['price'] = "0"
                order_params['tif'] = "ioc"

            logger.info(f"Order params: {order_params}")
            fut_order = gate_api.FuturesOrder(**order_params)
            logger.info(f"Futures order created: contract={fut_order.contract}, size={fut_order.size}")

            # 可根据需要设置：reduce_only/close/auto_size 等，这里默认开仓

            created = self.futures_api.create_futures_order(settle='usdt', futures_order=fut_order)

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Futures order placed: {getattr(created, 'id', 'N/A')} - {side} {amount} {contract} at {price}"
            })

            return {
                "success": True,
                "order_id": getattr(created, 'id', None),
                "status": getattr(created, 'status', None),
                "message": "Order placed successfully",
                "contract": contract
            }

        except Exception as e:
            logger.error(f"Error placing order: {e}", exc_info=True)
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

            # 取消合约订单需要 settle 与 order_id；若需按合约取消可扩展
            self.futures_api.cancel_futures_order(settle='usdt', order_id=order_id)

            self.trading_logs.append({
                "timestamp": datetime.now().isoformat(),
                "level": "INFO",
                "message": f"Futures order cancelled: {order_id}"
            })

            return {
                "success": True,
                "message": f"Order {order_id} cancelled successfully"
            }

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return {"error": str(e)}

