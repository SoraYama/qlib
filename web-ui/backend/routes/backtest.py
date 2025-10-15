#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Backtest API Routes
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

from services.qlib_service import QlibService

# Create blueprint
bp = Blueprint('backtest', __name__)

# Initialize service
qlib_service = QlibService()


@bp.route('/run', methods=['POST'])
def run_backtest():
    """运行回测"""
    try:
        config = request.json.get('config', {})

        # 默认配置
        default_config = {
            "start_time": "2024-12-01",
            "end_time": "2025-10-10",
            "initial_capital": 100000000,
            "benchmark": "btcusdt",
            "strategy": "TopkDropoutStrategy",
            "model_name": "lgb"
        }

        # 合并配置
        config = {**default_config, **config}

        # 运行回测
        result = qlib_service.run_backtest(config)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error running backtest: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/results/<result_id>', methods=['GET'])
def get_backtest_results(result_id):
    """获取回测结果"""
    try:
        results = qlib_service.get_backtest_results(result_id)
        return jsonify({
            "success": True,
            "data": results
        })
    except Exception as e:
        logger.error(f"Error getting backtest results: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/list', methods=['GET'])
def list_backtests():
    """列出所有回测结果"""
    try:
        backtests = qlib_service.list_backtests()
        return jsonify({
            "success": True,
            "data": backtests
        })
    except Exception as e:
        logger.error(f"Error listing backtests: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/delete/<result_id>', methods=['DELETE'])
def delete_backtest(result_id):
    """删除回测结果"""
    try:
        qlib_service.delete_backtest(result_id)
        return jsonify({
            "success": True,
            "message": f"Backtest {result_id} deleted successfully"
        })
    except Exception as e:
        logger.error(f"Error deleting backtest: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/export/<result_id>', methods=['GET'])
def export_backtest(result_id):
    """导出回测结果"""
    try:
        export_data = qlib_service.export_backtest(result_id)
        return jsonify({
            "success": True,
            "data": export_data
        })
    except Exception as e:
        logger.error(f"Error exporting backtest: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/compare', methods=['POST'])
def compare_backtests():
    """比较多个回测结果"""
    try:
        result_ids = request.json.get('result_ids', [])
        if not result_ids:
            return jsonify({
                "success": False,
                "error": "result_ids is required"
            }), 400

        comparison = qlib_service.compare_backtests(result_ids)

        return jsonify({
            "success": True,
            "data": comparison
        })
    except Exception as e:
        logger.error(f"Error comparing backtests: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/metrics/<result_id>', methods=['GET'])
def get_backtest_metrics(result_id):
    """获取回测指标"""
    try:
        metrics = qlib_service.get_backtest_metrics(result_id)
        return jsonify({
            "success": True,
            "data": metrics
        })
    except Exception as e:
        logger.error(f"Error getting backtest metrics: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/chart/<result_id>', methods=['GET'])
def get_backtest_chart(result_id):
    """获取回测图表数据"""
    try:
        chart_type = request.args.get('type', 'returns')  # returns, drawdown, positions
        chart_data = qlib_service.get_backtest_chart(result_id, chart_type)

        return jsonify({
            "success": True,
            "data": chart_data
        })
    except Exception as e:
        logger.error(f"Error getting backtest chart: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

