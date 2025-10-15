#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Management API Routes
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
try:
    from custom_scripts.model_manager import ModelManager
except ImportError:
    # 如果无法导入，创建一个模拟的ModelManager
    class ModelManager:
        def __init__(self):
            pass
        def list_models(self):
            return []
        def train_model(self, model_name, config):
            return {"status": "error", "message": "ModelManager not available"}

# Create blueprint
bp = Blueprint('model', __name__)

# Initialize services
qlib_service = QlibService()
model_manager = ModelManager()


@bp.route('/list', methods=['GET'])
def list_models():
    """列出所有可用模型"""
    try:
        models = model_manager.list_models()
        model_info = []

        for model_name in models:
            info = model_manager.get_model_info(model_name)
            model_info.append({
                "name": model_name,
                "class": info["class"],
                "description": info["description"],
                "tunable_params": len(info["tunable_params"])
            })

        return jsonify({
            "success": True,
            "data": model_info
        })
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/info/<model_name>', methods=['GET'])
def get_model_info(model_name):
    """获取模型详细信息"""
    try:
        info = model_manager.get_model_info(model_name)
        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        logger.error(f"Error getting model info: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/switch', methods=['POST'])
def switch_model():
    """切换模型"""
    try:
        model_name = request.json.get('model_name')
        if not model_name:
            return jsonify({
                "success": False,
                "error": "model_name is required"
            }), 400

        info = model_manager.switch_model(model_name)
        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        logger.error(f"Error switching model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/params/<model_name>', methods=['GET'])
def get_model_params(model_name):
    """获取模型参数"""
    try:
        info = model_manager.get_model_info(model_name)
        return jsonify({
            "success": True,
            "data": {
                "default_params": info["default_params"],
                "tunable_params": info["tunable_params"]
            }
        })
    except Exception as e:
        logger.error(f"Error getting model params: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/params/<model_name>', methods=['POST'])
def update_model_params(model_name):
    """更新模型参数"""
    try:
        params = request.json.get('params', {})
        if not params:
            return jsonify({
                "success": False,
                "error": "params is required"
            }), 400

        info = model_manager.update_params(model_name, params)
        return jsonify({
            "success": True,
            "data": info
        })
    except Exception as e:
        logger.error(f"Error updating model params: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/train', methods=['POST'])
def train_model():
    """训练模型"""
    try:
        model_name = request.json.get('model_name')
        params = request.json.get('params', {})

        if not model_name:
            return jsonify({
                "success": False,
                "error": "model_name is required"
            }), 400

        # 更新参数（如果有）
        if params:
            model_manager.update_params(model_name, params)

        # 创建训练配置
        config = model_manager.create_workflow_config(model_name)

        # 运行训练
        result = qlib_service.train_model(config)

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error training model: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/tune/<model_name>', methods=['POST'])
def tune_hyperparameters(model_name):
    """超参数调优"""
    try:
        n_trials = request.json.get('n_trials', 100)
        timeout = request.json.get('timeout', 3600)

        result = model_manager.run_hyperparameter_tuning(
            model_name,
            n_trials=n_trials,
            timeout=timeout
        )

        return jsonify({
            "success": True,
            "data": result
        })
    except Exception as e:
        logger.error(f"Error tuning hyperparameters: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/predict', methods=['POST'])
def predict():
    """模型预测"""
    try:
        model_name = request.json.get('model_name')
        data = request.json.get('data')

        if not model_name or not data:
            return jsonify({
                "success": False,
                "error": "model_name and data are required"
            }), 400

        predictions = qlib_service.predict(model_name, data)

        return jsonify({
            "success": True,
            "data": predictions
        })
    except Exception as e:
        logger.error(f"Error making predictions: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/performance/<model_name>', methods=['GET'])
def get_model_performance(model_name):
    """获取模型性能指标"""
    try:
        performance = qlib_service.get_model_performance(model_name)
        return jsonify({
            "success": True,
            "data": performance
        })
    except Exception as e:
        logger.error(f"Error getting model performance: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route('/compare', methods=['POST'])
def compare_models():
    """比较多个模型"""
    try:
        models = request.json.get('models', [])
        if not models:
            models = model_manager.list_models()

        comparison = model_manager.compare_models(models)

        return jsonify({
            "success": True,
            "data": comparison.to_dict('records')
        })
    except Exception as e:
        logger.error(f"Error comparing models: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

