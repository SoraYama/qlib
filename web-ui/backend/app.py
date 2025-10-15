#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Flask Backend API for Crypto Trading System
"""

import os
import sys
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from loguru import logger
import traceback
import pandas as pd

# Add parent directory to path for imports
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent))

# Import route modules
from routes import data, model, backtest, trading, dashboard

# Create Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Configuration
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Register blueprints
app.register_blueprint(data.bp, url_prefix='/api/data')
app.register_blueprint(model.bp, url_prefix='/api/model')
app.register_blueprint(backtest.bp, url_prefix='/api/backtest')
app.register_blueprint(trading.bp, url_prefix='/api/trading')
app.register_blueprint(dashboard.bp, url_prefix='/api/dashboard')


@app.route('/')
def index():
    """API 根路径"""
    return jsonify({
        "message": "Crypto Trading System API",
        "version": "1.0.0",
        "endpoints": {
            "data": "/api/data",
            "model": "/api/model",
            "backtest": "/api/backtest",
            "trading": "/api/trading",
            "dashboard": "/api/dashboard"
        }
    })


@app.route('/api/health')
def health_check():
    """健康检查端点"""
    return jsonify({
        "status": "healthy",
        "timestamp": str(pd.Timestamp.now())
    })


@app.errorhandler(404)
def not_found(error):
    """404 错误处理"""
    return jsonify({
        "error": "Not Found",
        "message": "The requested resource was not found"
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """500 错误处理"""
    logger.error(f"Internal server error: {error}")
    logger.error(traceback.format_exc())

    return jsonify({
        "error": "Internal Server Error",
        "message": "An unexpected error occurred"
    }), 500


@app.errorhandler(400)
def bad_request(error):
    """400 错误处理"""
    return jsonify({
        "error": "Bad Request",
        "message": "Invalid request parameters"
    }), 400


if __name__ == '__main__':
    # 配置日志
    logger.add("logs/app.log", rotation="1 day", retention="30 days")

    # 创建日志目录
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # 启动应用
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') == 'development'

    logger.info(f"Starting Flask app on port {port}")
    app.run(host='0.0.0.0', port=port, debug=debug)

