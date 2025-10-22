#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Model Manager for Qlib
Manages model switching, parameter tuning, and hyperparameter optimization
"""

import sys
import os
import yaml
import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger
import fire

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

try:
    import optuna
    OPTUNA_AVAILABLE = True
except ImportError:
    OPTUNA_AVAILABLE = False
    logger.warning("Optuna not available. Hyperparameter tuning will be disabled.")


class ModelManager:
    """模型管理器，支持模型切换和参数调优"""

    def __init__(self, config_dir: str = None):
        """
        初始化模型管理器

        Parameters
        ----------
        config_dir: str
            模型配置目录路径
        """
        self.config_dir = Path(config_dir) if config_dir else CUR_DIR / "model_configs"
        self.models = {}
        self.current_model = None
        self.best_params = {}

        # 加载所有模型配置
        self._load_model_configs()

        logger.info(f"ModelManager initialized with {len(self.models)} models")

    def _load_model_configs(self):
        """加载所有模型配置"""
        if not self.config_dir.exists():
            logger.error(f"Model config directory not found: {self.config_dir}")
            return

        for config_file in self.config_dir.glob("*.yaml"):
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)

                model_name = config_file.stem.replace("_config", "")
                self.models[model_name] = config
                logger.info(f"Loaded model config: {model_name}")

            except Exception as e:
                logger.error(f"Error loading config {config_file}: {e}")

    def list_models(self) -> List[str]:
        """列出所有可用模型"""
        return list(self.models.keys())

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """获取模型信息"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        config = self.models[model_name]
        return {
            "name": model_name,
            "class": config["model"]["class"],
            "module_path": config["model"]["module_path"],
            "description": config.get("description", ""),
            "tunable_params": config.get("tunable_params", {}),
            "default_params": config["model"]["kwargs"]
        }

    def switch_model(self, model_name: str) -> Dict[str, Any]:
        """切换模型"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        self.current_model = model_name
        logger.info(f"Switched to model: {model_name}")

        return self.get_model_info(model_name)

    def update_params(self, model_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """更新模型参数"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        # 验证参数
        tunable_params = self.models[model_name].get("tunable_params", {})
        for param_name, param_value in params.items():
            if param_name not in tunable_params:
                logger.warning(f"Parameter {param_name} is not tunable for {model_name}")
            else:
                # 检查参数值是否在允许范围内
                if isinstance(tunable_params[param_name], list):
                    if param_value not in tunable_params[param_name]:
                        logger.warning(f"Parameter {param_name} value {param_value} not in allowed range")

        # 更新参数
        self.models[model_name]["model"]["kwargs"].update(params)

        logger.info(f"Updated parameters for {model_name}: {params}")
        return self.get_model_info(model_name)

    def get_current_model_config(self) -> Dict[str, Any]:
        """获取当前模型配置"""
        if self.current_model is None:
            raise ValueError("No model selected")

        return self.models[self.current_model]

    def create_workflow_config(self, model_name: str = None, **kwargs) -> Dict[str, Any]:
        """创建完整的工作流配置"""
        if model_name is None:
            model_name = self.current_model

        if model_name is None:
            raise ValueError("No model specified")

        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        # 数据处理配置
        data_handler_config = {
            "start_time": "2024-01-01",
            "end_time": "2025-10-12",
            "fit_start_time": "2024-01-01",
            "fit_end_time": "2024-08-31",
            "instruments": "all",
            "infer_processors": [
                {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
                {"class": "Fillna", "kwargs": {"fields_group": "feature"}}
            ],
            "learn_processors": [
                {"class": "DropnaLabel"},
                {"class": "CSRankNorm", "kwargs": {"fields_group": "label"}}
            ],
            "label": ["Ref($close, -2) / Ref($close, -1) - 1"]
        }

        # 回测配置
        port_analysis_config = {
            "strategy": {
                "class": "TopkDropoutStrategy",
                "module_path": "qlib.contrib.strategy",
                "kwargs": {
                    "signal": "<PRED>",
                    "topk": 2,
                    "n_drop": 0
                }
            },
            "backtest": {
                "start_time": "2024-12-01",
                "end_time": "2025-10-10",
                "account": 100000000,
                "benchmark": "btcusdt",
                "exchange_kwargs": {
                    "limit_threshold": 0.095,
                    "deal_price": "close",
                    "open_cost": 0.001,
                    "close_cost": 0.001,
                    "min_cost": 0
                }
            }
        }

        # 基础配置
        config = {
            "qlib_init": {
                "provider_uri": "~/.qlib/qlib_data/crypto_data",
                "region": "cn"
            },
            "market": "all",
            "benchmark": "btcusdt",
            "data_handler_config": data_handler_config,
            "port_analysis_config": port_analysis_config,
            "task": {
                "model": self.models[model_name]["model"],
                "dataset": {
                    "class": "DatasetH",
                    "module_path": "qlib.data.dataset",
                    "kwargs": {
                        "handler": {
                            "class": "CryptoEnhancedHandler",
                            "module_path": "custom_scripts.crypto_enhanced_handler",
                            "kwargs": data_handler_config
                        },
                        "segments": {
                            "train": ["2024-01-01", "2024-08-31"],
                            "valid": ["2024-09-01", "2024-11-30"],
                            "test": ["2024-12-01", "2025-10-10"]
                        }
                    }
                },
                "record": [
                    {"class": "SignalRecord", "module_path": "qlib.workflow.record_temp", "kwargs": {}},
                    {"class": "SigAnaRecord", "module_path": "qlib.workflow.record_temp", "kwargs": {"ana_long_short": False, "ann_scaler": 365}},
                    {"class": "PortAnaRecord", "module_path": "qlib.workflow.record_temp", "kwargs": {"config": port_analysis_config}}
                ]
            }
        }

        # 应用自定义参数
        config.update(kwargs)

        return config

    def save_workflow_config(self, config: Dict[str, Any], output_path: str):
        """保存工作流配置到文件"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Workflow config saved to: {output_path}")

    def run_hyperparameter_tuning(
        self,
        model_name: str,
        n_trials: int = 100,
        timeout: int = 3600,
        study_name: str = None
    ) -> Dict[str, Any]:
        """运行超参数调优"""
        if not OPTUNA_AVAILABLE:
            raise ImportError("Optuna is required for hyperparameter tuning")

        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        tunable_params = self.models[model_name].get("tunable_params", {})
        if not tunable_params:
            logger.warning(f"No tunable parameters defined for {model_name}")
            return {}

        # 创建 Optuna 研究
        if study_name is None:
            study_name = f"{model_name}_tuning"

        study = optuna.create_study(
            direction="minimize",
            study_name=study_name,
            storage=f"sqlite:///{study_name}.db"
        )

        def objective(trial):
            # 为每个可调参数建议值
            params = {}
            for param_name, param_values in tunable_params.items():
                if isinstance(param_values, list):
                    if all(isinstance(v, (int, float)) for v in param_values):
                        # 数值参数
                        if all(isinstance(v, int) for v in param_values):
                            params[param_name] = trial.suggest_categorical(param_name, param_values)
                        else:
                            params[param_name] = trial.suggest_categorical(param_name, param_values)
                    else:
                        # 分类参数
                        params[param_name] = trial.suggest_categorical(param_name, param_values)
                else:
                    logger.warning(f"Unsupported parameter type for {param_name}")

            # 这里应该运行实际的训练和评估
            # 为了演示，我们返回一个随机值
            # 在实际实现中，应该：
            # 1. 更新模型参数
            # 2. 训练模型
            # 3. 在验证集上评估
            # 4. 返回损失值

            return np.random.random()  # 占位符

        # 运行优化
        study.optimize(objective, n_trials=n_trials, timeout=timeout)

        # 获取最佳参数
        best_params = study.best_params
        best_value = study.best_value

        self.best_params[model_name] = best_params

        logger.info(f"Hyperparameter tuning completed for {model_name}")
        logger.info(f"Best parameters: {best_params}")
        logger.info(f"Best value: {best_value}")

        return {
            "best_params": best_params,
            "best_value": best_value,
            "n_trials": len(study.trials),
            "study_name": study_name
        }

    def get_best_params(self, model_name: str) -> Dict[str, Any]:
        """获取最佳参数"""
        return self.best_params.get(model_name, {})

    def apply_best_params(self, model_name: str):
        """应用最佳参数"""
        best_params = self.get_best_params(model_name)
        if best_params:
            self.update_params(model_name, best_params)
            logger.info(f"Applied best parameters to {model_name}")
        else:
            logger.warning(f"No best parameters found for {model_name}")

    def compare_models(self, models: List[str] = None) -> pd.DataFrame:
        """比较多个模型的性能"""
        if models is None:
            models = self.list_models()

        comparison_data = []

        for model_name in models:
            try:
                model_info = self.get_model_info(model_name)
                comparison_data.append({
                    "Model": model_name,
                    "Class": model_info["class"],
                    "Tunable_Params": len(model_info["tunable_params"]),
                    "Description": model_info["description"][:100] + "..." if len(model_info["description"]) > 100 else model_info["description"]
                })
            except Exception as e:
                logger.error(f"Error getting info for {model_name}: {e}")

        return pd.DataFrame(comparison_data)

    def export_model_config(self, model_name: str, output_path: str):
        """导出模型配置"""
        if model_name not in self.models:
            raise ValueError(f"Model {model_name} not found")

        config = self.models[model_name]
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(config, f, default_flow_style=False, allow_unicode=True)

        logger.info(f"Model config exported to: {output_path}")

    def import_model_config(self, config_path: str, model_name: str = None):
        """导入模型配置"""
        config_path = Path(config_path)

        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        if model_name is None:
            model_name = config_path.stem.replace("_config", "")

        self.models[model_name] = config
        logger.info(f"Model config imported: {model_name}")


def main():
    """主函数"""
    manager = ModelManager()

    # 列出所有模型
    print("Available models:")
    for model in manager.list_models():
        print(f"  - {model}")

    # 获取模型信息
    if manager.list_models():
        first_model = manager.list_models()[0]
        info = manager.get_model_info(first_model)
        print(f"\nModel info for {first_model}:")
        print(f"  Class: {info['class']}")
        print(f"  Description: {info['description']}")
        print(f"  Tunable parameters: {len(info['tunable_params'])}")


if __name__ == "__main__":
    fire.Fire(ModelManager)

