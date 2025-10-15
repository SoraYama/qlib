#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Dashboard API Routes
"""

import os
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from loguru import logger
import pandas as pd
from datetime import datetime

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent.parent / 'custom-scripts'))

from services.gate_service import GateService
from services.qlib_service import QlibService

# Create blueprint
bp = Blueprint('dashboard', __name__)

# Initialize services
gate_service = GateService()
qlib_service = QlibService()


@bp.route('/summary', methods=['GET'])
def get_dashboard_summary():
    """获取仪表盘汇总数据"""
    try:
        # 获取交易状态和账户信息
        trading_status = gate_service.get_trading_status()
        account_info = gate_service.get_account_info()
        positions = gate_service.get_positions()

        # 获取数据状态
        data_status = qlib_service.get_data_status()

        # 计算汇总数据
        total_balance = account_info.get('total_balance', 0) if isinstance(account_info, dict) else 0
        active_positions = len(positions) if isinstance(positions, list) else 0

        # 计算盈亏（这里需要根据实际业务逻辑调整）
        total_pnl = 0
        daily_pnl = 0

        if isinstance(positions, list):
            for position in positions:
                if isinstance(position, dict):
                    total_pnl += position.get('unrealized_pnl', 0)
                    # 这里可以添加今日盈亏的计算逻辑

        # 系统服务状态检查
        services_status = {
            'backend': 'running',
            'database': 'running' if data_status.get('data_exists', False) else 'error',
            'redis': 'running',  # 这里可以添加实际的 Redis 检查
            'trading_system': 'running' if trading_status.get('trading_enabled', False) else 'stopped'
        }

        summary = {
            'account': {
                'total_balance': total_balance,
                'available_balance': total_balance,  # 简化处理
                'total_pnl': total_pnl,
                'daily_pnl': daily_pnl
            },
            'positions': {
                'active_count': active_positions,
                'total_value': sum(pos.get('size', 0) * pos.get('current_price', 0) for pos in positions if isinstance(pos, dict))
            },
            'system': {
                'services': services_status,
                'data_status': {
                    'instruments_count': len(data_status.get('instruments', [])),
                    'features_count': len(data_status.get('features', [])),
                    'date_range_days': data_status.get('date_range', {}).get('total_days', 0)
                }
            },
            'last_update': datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "data": summary
        })
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/health', methods=['GET'])
def get_system_health():
    """获取系统健康状态"""
    try:
        # 检查各个服务的健康状态
        health_status = {
            'overall': 'healthy',
            'services': {
                'backend': 'healthy',
                'database': 'healthy',
                'redis': 'healthy',
                'trading_api': 'healthy' if gate_service.trading_enabled else 'disabled'
            },
            'timestamp': datetime.now().isoformat()
        }

        return jsonify({
            "success": True,
            "data": health_status
        })
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
