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

    def __init__(self, save_dir: str, start: Optional[datetime] = None, end: Optional[datetime] = None,
                 delay: float = 0.5, interval: str = "1d", max_workers: int = 1,
                 max_collector_count: int = 2, check_data_length: Optional[int] = None,
                 limit_nums: Optional[int] = None, **kwargs):
        """
        Initialize base collector

        Parameters
        ----------
        save_dir : str
            Directory to save data
        start : datetime, optional
            Start date
        end : datetime, optional
            End date
        delay : float
            Delay between requests
        interval : str
            Data interval (e.g., '1d')
        max_workers : int
            Number of worker threads
        max_collector_count : int
            Maximum collection attempts
        check_data_length : int, optional
            Expected data length
        limit_nums : int, optional
            Limit number of instruments
        """
        self.save_dir = save_dir
        self.start = start or datetime.now()
        self.end = end or datetime.now()
        self.delay = delay
        self.interval = interval
        self.max_workers = max_workers
        self.max_collector_count = max_collector_count
        self.check_data_length = check_data_length
        self.limit_nums = limit_nums

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


# BaseRun implementation compatible with gate_collector.py
# Simplified version that matches the interface expected by Run class
class BaseRun(abc.ABC):
    """Base class for running data collection workflows"""

    def __init__(self, source_dir=None, normalize_dir=None, max_workers=1, interval="1d"):
        """
        Initialize base run class

        Parameters
        ----------
        source_dir : str, optional
            Source directory for raw data
        normalize_dir : str, optional
            Directory for normalized data
        max_workers : int, optional
            Number of worker threads
        interval : str, optional
            Data interval (e.g., '1d')
        """
        self.source_dir = source_dir
        self.normalize_dir = normalize_dir
        self.max_workers = max_workers
        self.interval = interval

    @property
    @abc.abstractmethod
    def collector_class_name(self):
        """Return the collector class name"""
        raise NotImplementedError("Subclass must implement collector_class_name")

    @property
    @abc.abstractmethod
    def normalize_class_name(self):
        """Return the normalize class name"""
        raise NotImplementedError("Subclass must implement normalize_class_name")

    @property
    @abc.abstractmethod
    def default_base_dir(self):
        """Return the default base directory"""
        raise NotImplementedError("Subclass must implement default_base_dir")

    def download_data(self, max_collector_count=2, delay=0, start=None, end=None,
                     check_data_length=None, limit_nums=None, **kwargs):
        """
        Download data - to be overridden by subclasses

        Parameters
        ----------
        max_collector_count : int
            Maximum collection attempts
        delay : float
            Delay between requests
        start : str
            Start date
        end : str
            End date
        check_data_length : int, optional
            Expected data length
        limit_nums : int, optional
            Limit number of instruments
        """
        raise NotImplementedError("Subclass must implement download_data")

    def normalize_data(self, date_field_name="date", symbol_field_name="symbol", **kwargs):
        """
        Normalize data - to be overridden by subclasses

        Parameters
        ----------
        date_field_name : str
            Name of date field
        symbol_field_name : str
            Name of symbol field
        """
        raise NotImplementedError("Subclass must implement normalize_data")
