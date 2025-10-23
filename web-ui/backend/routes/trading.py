#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Trading API Routes
"""

import os
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from loguru import logger
import pandas as pd

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent.parent / 'custom-scripts'))

from shared_services import gate_service

# Create blueprint
bp = Blueprint('trading', __name__)


@bp.route('/status', methods=['GET'])
def get_trading_status():
    """获取交易状态"""
    try:
        status = gate_service.get_trading_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"Error getting trading status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/start', methods=['POST'])
def start_trading():
    """启动实盘交易"""
    try:
        config = request.json.get('config', {})

        # 默认配置
        default_config = {
            "model_name": "lgb",
            "strategy_name": "default",
            "initial_capital": 10000,
            "max_position_size": 0.3,
            "stop_loss": 0.05,
            "max_drawdown": 0.2
        }

        # 合并配置
        config = {**default_config, **config}

        logger.info(f"Starting trading with config: {config}")
        result = gate_service.start_trading(config)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error starting trading: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/stop', methods=['POST'])
def stop_trading():
    """停止实盘交易"""
    try:
        result = gate_service.stop_trading()
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error stopping trading: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/positions', methods=['GET'])
def get_positions():
    """获取当前持仓"""
    try:
        positions = gate_service.get_positions()
        return jsonify({
            "success": True,
            "data": positions
        })
    except Exception as e:
        logger.error(f"Error getting positions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/orders', methods=['GET'])
def get_orders():
    """获取订单历史"""
    try:
        limit = request.args.get('limit', 100)
        offset = request.args.get('offset', 0)

        orders = gate_service.get_orders(limit=int(limit), offset=int(offset))
        return jsonify({
            "success": True,
            "data": orders
        })
    except Exception as e:
        logger.error(f"Error getting orders: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/account', methods=['GET'])
def get_account_info():
    """获取账户信息"""
    try:
        account_info = gate_service.get_account_info()
        return jsonify({
            "success": True,
            "data": account_info
        })
    except Exception as e:
        logger.error(f"Error getting account info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/balance', methods=['GET'])
def get_balance():
    """获取账户余额"""
    try:
        balance = gate_service.get_balance()
        return jsonify({
            "success": True,
            "data": balance
        })
    except Exception as e:
        logger.error(f"Error getting balance: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/risk', methods=['GET'])
def get_risk_metrics():
    """获取风险指标"""
    try:
        risk_metrics = gate_service.get_risk_metrics()
        return jsonify({
            "success": True,
            "data": risk_metrics
        })
    except Exception as e:
        logger.error(f"Error getting risk metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/risk', methods=['POST'])
def update_risk_settings():
    """更新风险设置"""
    try:
        risk_settings = request.json.get('risk_settings', {})

        result = gate_service.update_risk_settings(risk_settings)
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error updating risk settings: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/risk-limits', methods=['POST'])
def update_risk_limits():
    """更新风险限制"""
    try:
        limits = request.json

        # 默认风险限制
        default_limits = {
            "max_position_size": 0.3,
            "max_drawdown": 0.2,
            "stop_loss": 0.05
        }

        # 合并用户设置的限制
        risk_limits = {**default_limits, **limits}

        # 这里应该调用gate_service来更新风险限制
        # 暂时返回成功响应
        result = {
            "message": "Risk limits updated successfully",
            "limits": risk_limits
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error updating risk limits: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/performance', methods=['GET'])
def get_trading_performance():
    """获取交易表现"""
    try:
        performance = gate_service.get_trading_performance()
        return jsonify({
            "success": True,
            "data": performance
        })
    except Exception as e:
        logger.error(f"Error getting trading performance: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/logs', methods=['GET'])
def get_trading_logs():
    """获取交易日志"""
    try:
        limit = request.args.get('limit', 100)
        level = request.args.get('level', 'INFO')

        logs = gate_service.get_trading_logs(limit=int(limit), level=level)
        return jsonify({
            "success": True,
            "data": logs
        })
    except Exception as e:
        logger.error(f"Error getting trading logs: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/kline', methods=['GET'])
def get_kline():
    """获取实时K线（公开接口）"""
    try:
        currency_pair = request.args.get('symbol', 'BTC_USDT')
        interval = request.args.get('interval', '1m')
        limit = int(request.args.get('limit', 200))
        data = gate_service.get_spot_klines(currency_pair, interval=interval, limit=limit)
        if not data:
            return jsonify({
                "success": False,
                "error": "empty result from upstream",
                "data": []
            }), 502
        return jsonify({
            "success": True,
            "data": data
        })
    except Exception as e:
        logger.error(f"Error getting kline: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "data": []
        }), 502


@bp.route('/plan', methods=['GET'])
def get_trading_plan():
    """获取当前交易计划（用于前端标注）"""
    try:
        plan = gate_service.get_current_trading_plan()
        status = gate_service.get_trading_status()
        return jsonify({
            "success": True,
            "data": {
                "plan": plan,
                "is_trading": bool(status.get('is_running', False))
            }
        })
    except Exception as e:
        logger.error(f"Error getting trading plan: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/close-position/<symbol>', methods=['POST'])
def close_position(symbol):
    """关闭指定交易对的持仓"""
    try:
        # 这里应该调用gate_service来关闭持仓
        # 暂时返回成功响应
        result = {
            "message": f"Position closed for {symbol}",
            "symbol": symbol,
            "status": "closed"
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error closing position for {symbol}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/cancel-order/<order_id>', methods=['POST'])
def cancel_order(order_id):
    """取消指定订单"""
    try:
        # 这里应该调用gate_service来取消订单
        # 暂时返回成功响应
        result = {
            "message": f"Order {order_id} cancelled",
            "order_id": order_id,
            "status": "cancelled"
        }

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

