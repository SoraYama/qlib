#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
On-chain Data Collector for Qlib (DISABLED)
This module has been completely disabled as requested by user.
链上数据采集功能已完全禁用
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
from loguru import logger

# Add parent directory to path to import base classes
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent / "scripts" / "data_collector"))

try:
    from base import BaseCollector, BaseNormalize, BaseRun
except ImportError:
    # 如果无法导入基础类，创建占位符
    class BaseCollector:
        pass
    class BaseNormalize:
        pass
    class BaseRun:
        pass


class OnchainCollector(BaseCollector):
    """链上数据采集器（已完全禁用）"""

    def __init__(self, *args, **kwargs):
        """初始化时直接抛出异常，表示功能已禁用"""
        logger.error("链上数据采集功能已被完全禁用")
        raise NotImplementedError(
            "链上数据采集功能已被禁用。\n"
            "请从以下位置移除相关调用：\n"
            "1. 数据采集脚本\n"
            "2. 工作流配置\n"
            "3. 特征处理器中的链上数据引用"
        )

    def get_data(self, *args, **kwargs):
        """获取数据方法已禁用"""
        raise NotImplementedError("链上数据采集功能已被禁用")

    def download_data(self, *args, **kwargs):
        """下载数据方法已禁用"""
        raise NotImplementedError("链上数据采集功能已被禁用")

    def normalize_data(self, *args, **kwargs):
        """数据标准化方法已禁用"""
        raise NotImplementedError("链上数据采集功能已被禁用")


class OnchainNormalize(BaseNormalize):
    """链上数据标准化器（已完全禁用）"""

    def __init__(self, *args, **kwargs):
        """初始化时直接抛出异常，表示功能已禁用"""
        logger.error("链上数据标准化功能已被完全禁用")
        raise NotImplementedError("链上数据标准化功能已被禁用")


class OnchainRun(BaseRun):
    """链上数据运行器（已完全禁用）"""

    def __init__(self, *args, **kwargs):
        """初始化时直接抛出异常，表示功能已禁用"""
        logger.error("链上数据运行功能已被完全禁用")
        raise NotImplementedError("链上数据运行功能已被禁用")


# 提供占位符函数，避免导入错误
def create_onchain_collector(*args, **kwargs):
    """创建链上数据采集器（已禁用）"""
    raise NotImplementedError("链上数据采集功能已被禁用")


def run_onchain_collection(*args, **kwargs):
    """运行链上数据采集（已禁用）"""
    raise NotImplementedError("链上数据采集功能已被禁用")


if __name__ == "__main__":
    print("链上数据采集功能已被完全禁用")
    print("如需使用，请配置相应的 API 密钥并重新启用相关代码")
