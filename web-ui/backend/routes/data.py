#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Management API Routes
"""

import os
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify
from loguru import logger
import pandas as pd
import subprocess

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent.parent / 'custom-scripts'))

from services.qlib_service import QlibService

# Create blueprint
bp = Blueprint('data', __name__)

# Initialize service
qlib_service = QlibService()


@bp.route('/status', methods=['GET'])
def get_data_status():
    """获取数据状态"""
    try:
        status = qlib_service.get_data_status()
        return jsonify({
            "success": True,
            "data": status
        })
    except Exception as e:
        logger.error(f"Error getting data status: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/update', methods=['POST'])
def update_data():
    """更新数据"""
    try:
        data_type = request.json.get('type', 'all')  # 'price', 'onchain', 'news', 'all'

        if data_type == 'all':
            # 更新所有数据
            result = qlib_service.update_all_data()
        elif data_type == 'price':
            result = qlib_service.update_price_data()
        elif data_type == 'onchain':
            result = qlib_service.update_onchain_data()
        elif data_type == 'news':
            result = qlib_service.update_news_data()
        else:
            return jsonify({
                "success": False,
                "error": f"Invalid data type: {data_type}"
            }), 400

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error updating data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/quality', methods=['GET'])
def check_data_quality():
    """检查数据质量"""
    try:
        quality_report = qlib_service.check_data_quality()
        return jsonify({
            "success": True,
            "data": quality_report
        })
    except Exception as e:
        logger.error(f"Error checking data quality: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/instruments', methods=['GET'])
def get_instruments():
    """获取交易对列表"""
    try:
        instruments = qlib_service.get_instruments()
        return jsonify({
            "success": True,
            "data": instruments
        })
    except Exception as e:
        logger.error(f"Error getting instruments: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/features', methods=['GET'])
def get_features():
    """获取特征列表"""
    try:
        features = qlib_service.get_features()
        return jsonify({
            "success": True,
            "data": features
        })
    except Exception as e:
        logger.error(f"Error getting features: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/download/<data_type>', methods=['POST'])
def download_data(data_type):
    """下载指定类型的数据"""
    try:
        start_date = request.json.get('start_date', '2024-01-01')
        end_date = request.json.get('end_date', '2025-10-12')

        if data_type == 'onchain':
            result = qlib_service.download_onchain_data(start_date, end_date)
        elif data_type == 'news':
            result = qlib_service.download_news_data(start_date, end_date)
        else:
            return jsonify({
                "success": False,
                "error": f"Invalid data type: {data_type}"
            }), 400

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error downloading {data_type} data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/merge', methods=['POST'])
def merge_data():
    """合并数据"""
    try:
        result = qlib_service.merge_all_data()
        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error merging data: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

