#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Base classes for data collection
Simplified version for custom scripts
"""

import abc
import pandas as pd
from datetime import datetime
from typing import Optional, List, Dict, Any
from loguru import logger


class BaseCollector(abc.ABC):
    """Base class for data collectors"""

    def __init__(self, save_dir: str, start: Optional[datetime] = None, end: Optional[datetime] = None, delay: float = 0.5):
        self.save_dir = save_dir
        self.start = start or datetime.now()
        self.end = end or datetime.now()
        self.delay = delay

    @abc.abstractmethod
    def download_data(self):
        """Download data - to be implemented by subclasses"""
        pass


class BaseNormalize(abc.ABC):
    """Base class for data normalization"""

    def __init__(self, source_dir: str, normalize_dir: str):
        self.source_dir = source_dir
        self.normalize_dir = normalize_dir

    @abc.abstractmethod
    def normalize(self):
        """Normalize data - to be implemented by subclasses"""
        pass


class BaseRun(abc.ABC):
    """Base class for running data collection workflows"""

    def __init__(self, **kwargs):
        self.kwargs = kwargs

    @abc.abstractmethod
    def run(self):
        """Run the workflow - to be implemented by subclasses"""
        pass
