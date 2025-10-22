#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
共享服务实例 - 确保所有路由使用相同的服务实例
"""

from services.qlib_service import QlibService
from services.gate_service import GateService

# 创建单例服务实例
qlib_service = QlibService()
gate_service = GateService()


