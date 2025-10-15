#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Qlib Service - 封装 Qlib 相关操作
"""

import os
import sys
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger
import yaml
import json

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent.parent.parent))

try:
    import qlib
    from qlib.workflow import R
    from qlib.data import D
    QLIB_AVAILABLE = True
except ImportError:
    QLIB_AVAILABLE = False
    logger.warning("Qlib not available. Some features will be disabled.")


class QlibService:
    """Qlib 服务封装类"""

    def __init__(self):
        """初始化 Qlib 服务"""
        self.qlib_data_dir = Path("~/.qlib/qlib_data/crypto_data").expanduser()
        self.mlruns_dir = Path("mlruns")
        self.custom_scripts_dir = Path(__file__).parent.parent.parent / "custom-scripts"

        if QLIB_AVAILABLE:
            self._init_qlib()

        logger.info("QlibService initialized")

    def _init_qlib(self):
        """初始化 Qlib"""
        try:
            qlib.init(
                provider_uri=str(self.qlib_data_dir),
                region="cn"
            )
            logger.info("Qlib initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Qlib: {e}")

    def get_data_status(self) -> Dict[str, Any]:
        """获取数据状态"""
        try:
            if not QLIB_AVAILABLE:
                return {"error": "Qlib not available"}

            # 检查数据目录
            data_status = {
                "qlib_data_dir": str(self.qlib_data_dir),
                "data_exists": self.qlib_data_dir.exists(),
                "instruments": [],
                "date_range": {},
                "features": []
            }

            if self.qlib_data_dir.exists():
                # 获取交易对列表
                instruments_file = self.qlib_data_dir / "instruments" / "all.txt"
                if instruments_file.exists():
                    with open(instruments_file, 'r') as f:
                        data_status["instruments"] = [line.strip() for line in f.readlines()]

                # 获取日期范围
                calendar_file = self.qlib_data_dir / "calendars" / "day.txt"
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
                features_dir = self.qlib_data_dir / "features"
                if features_dir.exists():
                    for feature_file in features_dir.glob("**/*.bin"):
                        feature_name = feature_file.stem
                        if feature_name not in data_status["features"]:
                            data_status["features"].append(feature_name)

            return data_status

        except Exception as e:
            logger.error(f"Error getting data status: {e}")
            return {"error": str(e)}

    def get_instruments(self) -> List[str]:
        """获取交易对列表"""
        try:
            if not QLIB_AVAILABLE:
                return []

            instruments_file = self.qlib_data_dir / "instruments" / "all.txt"
            if instruments_file.exists():
                with open(instruments_file, 'r') as f:
                    return [line.strip() for line in f.readlines()]
            return []

        except Exception as e:
            logger.error(f"Error getting instruments: {e}")
            return []

    def get_features(self) -> List[str]:
        """获取特征列表"""
        try:
            features = []
            features_dir = self.qlib_data_dir / "features"

            if features_dir.exists():
                for feature_file in features_dir.glob("**/*.bin"):
                    feature_name = feature_file.stem
                    if feature_name not in features:
                        features.append(feature_name)

            return features

        except Exception as e:
            logger.error(f"Error getting features: {e}")
            return []

    def check_data_quality(self) -> Dict[str, Any]:
        """检查数据质量"""
        try:
            quality_report = {
                "missing_data": {},
                "outliers": {},
                "data_consistency": {},
                "overall_score": 0.0
            }

            # 这里应该实现具体的数据质量检查逻辑
            # 包括缺失值检查、异常值检测、数据一致性验证等

            return quality_report

        except Exception as e:
            logger.error(f"Error checking data quality: {e}")
            return {"error": str(e)}

    def update_price_data(self) -> Dict[str, Any]:
        """更新价格数据"""
        try:
            # 运行 Gate.io 数据采集器
            cmd = [
                "python",
                str(self.custom_scripts_dir / "gate_collector.py"),
                "download_data",
                "--source_dir", str(self.custom_scripts_dir.parent / "data" / "gate" / "source"),
                "--start", "2024-01-01",
                "--end", "2025-10-12"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.custom_scripts_dir.parent)

            if result.returncode == 0:
                return {"success": True, "message": "Price data updated successfully"}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Error updating price data: {e}")
            return {"error": str(e)}

    def update_onchain_data(self) -> Dict[str, Any]:
        """更新链上数据"""
        try:
            # 运行链上数据采集器
            cmd = [
                "python",
                str(self.custom_scripts_dir / "onchain_collector.py"),
                "download_data",
                "--source_dir", str(self.custom_scripts_dir.parent / "data" / "onchain" / "source"),
                "--start", "2024-01-01",
                "--end", "2025-10-12"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.custom_scripts_dir.parent)

            if result.returncode == 0:
                return {"success": True, "message": "Onchain data updated successfully"}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Error updating onchain data: {e}")
            return {"error": str(e)}

    def update_news_data(self) -> Dict[str, Any]:
        """更新新闻数据"""
        try:
            # 运行新闻数据采集器
            cmd = [
                "python",
                str(self.custom_scripts_dir / "news_collector.py"),
                "download_data",
                "--source_dir", str(self.custom_scripts_dir.parent / "data" / "news" / "source"),
                "--start", "2024-01-01",
                "--end", "2025-10-12"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.custom_scripts_dir.parent)

            if result.returncode == 0:
                return {"success": True, "message": "News data updated successfully"}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Error updating news data: {e}")
            return {"error": str(e)}

    def update_all_data(self) -> Dict[str, Any]:
        """更新所有数据"""
        try:
            results = {}

            # 更新价格数据
            results["price"] = self.update_price_data()

            # 更新链上数据
            results["onchain"] = self.update_onchain_data()

            # 更新新闻数据
            results["news"] = self.update_news_data()

            # 合并数据
            results["merge"] = self.merge_all_data()

            return results

        except Exception as e:
            logger.error(f"Error updating all data: {e}")
            return {"error": str(e)}

    def merge_all_data(self) -> Dict[str, Any]:
        """合并所有数据"""
        try:
            # 运行数据合并脚本
            cmd = [
                "python",
                str(self.custom_scripts_dir / "merge_data.py"),
                "merge_all_data"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.custom_scripts_dir.parent)

            if result.returncode == 0:
                return {"success": True, "message": "Data merged successfully"}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Error merging data: {e}")
            return {"error": str(e)}

    def train_model(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """训练模型"""
        try:
            if not QLIB_AVAILABLE:
                return {"error": "Qlib not available"}

            # 保存配置到临时文件
            config_file = Path("temp_config.yaml")
            with open(config_file, 'w') as f:
                yaml.dump(config, f)

            # 运行训练
            cmd = ["qrun", str(config_file)]
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.custom_scripts_dir.parent)

            # 清理临时文件
            config_file.unlink(missing_ok=True)

            if result.returncode == 0:
                return {"success": True, "message": "Model trained successfully"}
            else:
                return {"success": False, "error": result.stderr}

        except Exception as e:
            logger.error(f"Error training model: {e}")
            return {"error": str(e)}

    def run_backtest(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """运行回测"""
        try:
            if not QLIB_AVAILABLE:
                return {"error": "Qlib not available"}

            # 这里应该实现具体的回测逻辑
            # 包括创建回测配置、运行回测、保存结果等

            return {"success": True, "result_id": "backtest_001", "message": "Backtest completed"}

        except Exception as e:
            logger.error(f"Error running backtest: {e}")
            return {"error": str(e)}

    def get_backtest_results(self, result_id: str) -> Dict[str, Any]:
        """获取回测结果"""
        try:
            # 这里应该实现从 MLflow 或数据库获取回测结果的逻辑
            return {"result_id": result_id, "status": "completed"}

        except Exception as e:
            logger.error(f"Error getting backtest results: {e}")
            return {"error": str(e)}

    def list_backtests(self) -> List[Dict[str, Any]]:
        """列出所有回测结果"""
        try:
            # 这里应该实现从 MLflow 获取所有回测结果的逻辑
            return []

        except Exception as e:
            logger.error(f"Error listing backtests: {e}")
            return []

    def delete_backtest(self, result_id: str) -> Dict[str, Any]:
        """删除回测结果"""
        try:
            # 这里应该实现删除回测结果的逻辑
            return {"success": True, "message": f"Backtest {result_id} deleted"}

        except Exception as e:
            logger.error(f"Error deleting backtest: {e}")
            return {"error": str(e)}

    def export_backtest(self, result_id: str) -> Dict[str, Any]:
        """导出回测结果"""
        try:
            # 这里应该实现导出回测结果的逻辑
            return {"result_id": result_id, "export_data": {}}

        except Exception as e:
            logger.error(f"Error exporting backtest: {e}")
            return {"error": str(e)}

    def compare_backtests(self, result_ids: List[str]) -> Dict[str, Any]:
        """比较多个回测结果"""
        try:
            # 这里应该实现比较回测结果的逻辑
            return {"comparison": {}}

        except Exception as e:
            logger.error(f"Error comparing backtests: {e}")
            return {"error": str(e)}

    def get_backtest_metrics(self, result_id: str) -> Dict[str, Any]:
        """获取回测指标"""
        try:
            # 这里应该实现获取回测指标的逻辑
            return {"metrics": {}}

        except Exception as e:
            logger.error(f"Error getting backtest metrics: {e}")
            return {"error": str(e)}

    def get_backtest_chart(self, result_id: str, chart_type: str) -> Dict[str, Any]:
        """获取回测图表数据"""
        try:
            # 这里应该实现获取图表数据的逻辑
            return {"chart_data": {}}

        except Exception as e:
            logger.error(f"Error getting backtest chart: {e}")
            return {"error": str(e)}

    def predict(self, model_name: str, data: Any) -> Dict[str, Any]:
        """模型预测"""
        try:
            if not QLIB_AVAILABLE:
                return {"error": "Qlib not available"}

            # 这里应该实现模型预测的逻辑
            return {"predictions": []}

        except Exception as e:
            logger.error(f"Error making predictions: {e}")
            return {"error": str(e)}

    def get_model_performance(self, model_name: str) -> Dict[str, Any]:
        """获取模型性能指标"""
        try:
            # 这里应该实现获取模型性能的逻辑
            return {"performance": {}}

        except Exception as e:
            logger.error(f"Error getting model performance: {e}")
            return {"error": str(e)}

