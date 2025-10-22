#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Enhanced Crypto Data Handler for Qlib
Integrates price data and news sentiment features (on-chain data removed)
"""

import sys
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger

# Add parent directory to path to import Qlib modules
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

from qlib.contrib.data.handler import Alpha158
from qlib.contrib.data.loader import Alpha158DL


class CryptoEnhancedHandler(Alpha158):
    """增强版加密货币数据处理器，整合价格和新闻特征（链上数据已移除）"""

    def __init__(
        self,
        instruments="all",
        start_time=None,
        end_time=None,
        freq="day",
        infer_processors=None,
        learn_processors=None,
        fit_start_time=None,
        fit_end_time=None,
        process_type="append",  # 默认使用append模式
        filter_pipe=None,
        inst_processors=None,
        **kwargs,
    ):
        """
        初始化增强版处理器

        Parameters
        ----------
        instruments: str or list
            交易对列表，默认 "all"
        start_time: str
            开始时间
        end_time: str
            结束时间
        freq: str
            数据频率，默认 "day"
        infer_processors: list
            推理时数据处理器
        learn_processors: list
            训练时数据处理器
        fit_start_time: str
            拟合开始时间
        fit_end_time: str
            拟合结束时间
        process_type: str
            处理类型
        filter_pipe: object
            过滤管道
        inst_processors: list
            工具处理器
        **kwargs: dict
            其他参数
        """
        # 设置默认处理器
        if infer_processors is None:
            infer_processors = [
                {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
                {"class": "Fillna", "kwargs": {"fields_group": "feature"}},
            ]

        if learn_processors is None:
            learn_processors = [
                {"class": "DropnaLabel"},
                {"class": "CSRankNorm", "kwargs": {"fields_group": "label"}},
            ]

        super().__init__(
            instruments=instruments,
            start_time=start_time,
            end_time=end_time,
            freq=freq,
            infer_processors=infer_processors,
            learn_processors=learn_processors,
            fit_start_time=fit_start_time,
            fit_end_time=fit_end_time,
            process_type=process_type,
            filter_pipe=filter_pipe,
            inst_processors=inst_processors,
            **kwargs,
        )

        logger.info("CryptoEnhancedHandler initialized with enhanced features")

    def get_feature_config(self):
        """获取增强特征配置"""
        # 1. 获取基础 Alpha158 特征
        base_fields, base_names = super().get_feature_config()

        # 2. 添加新闻情绪特征（链上数据已移除）
        sentiment_fields, sentiment_names = self._get_sentiment_features()

        # 3. 添加衍生特征
        derived_fields, derived_names = self._get_derived_features()

        # 4. 合并所有特征
        all_fields = base_fields + sentiment_fields + derived_fields
        all_names = base_names + sentiment_names + derived_names

        logger.info(f"Total features: {len(all_fields)} (Base: {len(base_fields)}, "
                   f"Sentiment: {len(sentiment_fields)}, "
                   f"Derived: {len(derived_fields)})")

        return all_fields, all_names


    def _get_sentiment_features(self):
        """获取新闻情绪特征"""
        fields = []
        names = []

        # 基础情绪指标
        sentiment_metrics = [
            "$sentiment_score",     # 情绪得分
            "$news_volume",         # 新闻数量
            "$weighted_sentiment",  # 加权情绪
        ]

        for metric in sentiment_metrics:
            fields.append(metric)
            names.append(metric.replace("$", "").upper())

        # 情绪指标的时间序列特征
        time_windows = [3, 7, 14]

        for metric in sentiment_metrics:
            for window in time_windows:
                # 移动平均
                fields.append(f"Mean({metric}, {window})")
                names.append(f"{metric.replace('$', '').upper()}_MA{window}")

                # 移动标准差
                fields.append(f"Std({metric}, {window})")
                names.append(f"{metric.replace('$', '').upper()}_STD{window}")

        # 情绪相对指标
        fields.extend([
            "$news_volume / Mean($news_volume, 30)",  # 新闻量比率
            "$sentiment_score / Std($sentiment_score, 7)",  # 情绪标准化得分
        ])
        names.extend([
            "NEWS_VOLUME_RATIO",
            "SENTIMENT_NORMALIZED",
        ])

        return fields, names

    def _get_derived_features(self):
        """获取衍生特征（结合多个数据源）"""
        fields = []
        names = []

        # 价格与链上数据的交互特征（已移除）

        # 价格与情绪的交互特征
        price_sentiment_features = [
            "$close * $sentiment_score",  # 价格与情绪乘积
            "$volume * $news_volume",     # 交易量与新闻量乘积
        ]

        for feature in price_sentiment_features:
            fields.append(feature)
            names.append(feature.replace("$", "").replace("*", "_").replace(" ", "_").upper())

        # 链上与情绪的交互特征（已移除）

        # 市场状态特征（链上数据已移除）
        market_state_features = [
            "If($sentiment_score > 0.5, 1, 0)",  # 高情绪状态
        ]

        for feature in market_state_features:
            fields.append(feature)
            names.append(feature.replace("$", "").replace(" ", "_").replace(",", "").upper())

        return fields, names

    def get_label_config(self):
        """获取标签配置（预测未来2日收益率）"""
        return ["Ref($close, -2) / Ref($close, -1) - 1"], ["LABEL0"]


class CryptoEnhancedHandlerVwap(CryptoEnhancedHandler):
    """使用 VWAP 作为标签的增强处理器"""

    def get_label_config(self):
        """获取标签配置（预测未来2日VWAP收益率）"""
        return ["Ref($vwap, -2) / Ref($vwap, -1) - 1"], ["LABEL0"]


class CryptoEnhancedHandlerMulti(CryptoEnhancedHandler):
    """多标签增强处理器（预测多个时间窗口的收益率）"""

    def get_label_config(self):
        """获取多标签配置"""
        labels = []
        names = []

        # 预测不同时间窗口的收益率
        windows = [1, 2, 3, 5, 10]

        for window in windows:
            labels.append(f"Ref($close, -{window}) / Ref($close, -1) - 1")
            names.append(f"LABEL{window}D")

        return labels, names


def create_enhanced_handler_config(
    instruments="all",
    start_time="2024-01-01",
    end_time="2025-10-12",
    fit_start_time="2024-01-01",
    fit_end_time="2024-08-31",
    label_type="close",  # "close", "vwap", "multi"
    **kwargs
):
    """创建增强处理器的配置

    Parameters
    ----------
    instruments: str or list
        交易对列表
    start_time: str
        开始时间
    end_time: str
        结束时间
    fit_start_time: str
        拟合开始时间
    fit_end_time: str
        拟合结束时间
    label_type: str
        标签类型："close", "vwap", "multi"
    **kwargs: dict
        其他参数

    Returns
    -------
    dict: 处理器配置
    """
    # 选择处理器类
    if label_type == "vwap":
        handler_class = "CryptoEnhancedHandlerVwap"
    elif label_type == "multi":
        handler_class = "CryptoEnhancedHandlerMulti"
    else:
        handler_class = "CryptoEnhancedHandler"

    config = {
        "class": handler_class,
        "module_path": "custom_scripts.crypto_enhanced_handler",
        "kwargs": {
            "instruments": instruments,
            "start_time": start_time,
            "end_time": end_time,
            "fit_start_time": fit_start_time,
            "fit_end_time": fit_end_time,
            "freq": "day",
            "infer_processors": [
                {"class": "RobustZScoreNorm", "kwargs": {"fields_group": "feature", "clip_outlier": True}},
                {"class": "Fillna", "kwargs": {"fields_group": "feature"}},
            ],
            "learn_processors": [
                {"class": "DropnaLabel"},
                {"class": "CSRankNorm", "kwargs": {"fields_group": "label"}},
            ],
            **kwargs
        }
    }

    return config


if __name__ == "__main__":
    # 测试增强处理器
    import qlib

    # 初始化 Qlib
    qlib.init(provider_uri="~/.qlib/qlib_data/crypto_data", region="cn")

    # 创建增强处理器
    handler = CryptoEnhancedHandler(
        instruments="all",
        start_time="2024-01-01",
        end_time="2024-12-31"
    )

    # 获取特征配置
    fields, names = handler.get_feature_config()

    print(f"Total features: {len(fields)}")
    print(f"Feature names: {names[:10]}...")  # 显示前10个特征名

    # 测试数据加载
    try:
        data = handler.fetch()
        print(f"Data shape: {data.shape}")
        print(f"Data columns: {list(data.columns)[:10]}...")  # 显示前10个列名
    except Exception as e:
        print(f"Data loading error: {e}")
        print("This is expected if onchain and news data are not available yet")

