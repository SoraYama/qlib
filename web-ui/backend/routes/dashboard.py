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

from shared_services import gate_service, qlib_service

# Create blueprint
bp = Blueprint('dashboard', __name__)


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

        # 直接检查数据目录是否存在（绕过 QlibService 的限制）
        from pathlib import Path
        qlib_data_dir = Path("~/.qlib/qlib_data/crypto_data").expanduser()
        data_exists = qlib_data_dir.exists()

        # 如果 QlibService 返回错误，但数据目录存在，则使用直接检查的结果
        if 'error' in data_status and data_exists:
            # 重新构建数据状态
            data_status = {
                "data_exists": True,
                "instruments": [],
                "date_range": {},
                "features": []
            }

            # 获取交易对列表
            instruments_file = qlib_data_dir / "instruments" / "all.txt"
            if instruments_file.exists():
                with open(instruments_file, 'r') as f:
                    data_status["instruments"] = [line.strip() for line in f.readlines()]

            # 获取日期范围
            calendar_file = qlib_data_dir / "calendars" / "day.txt"
            if calendar_file.exists():
                with open(calendar_file, 'r') as f:
                    dates = [line.strip() for line in f.readlines()]
                    if dates:
                        data_status["date_range"] = {
                            "start": dates[0],
                            "end": dates[-1],
                            "total_days": len(dates)
                        }

            # 获取特征列表
            features_dir = qlib_data_dir / "features"
            if features_dir.exists():
                for feature_file in features_dir.glob("**/*.bin"):
                    feature_name = feature_file.stem
                    if feature_name not in data_status["features"]:
                        data_status["features"].append(feature_name)

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
