#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gate.io Data Collector for Qlib
Collects spot trading data for ETH/USDT and BTC/USDT
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import time

import fire
import pandas as pd
from loguru import logger
from dotenv import load_dotenv
import gate_api
from gate_api import ApiClient, Configuration, SpotApi

# Add parent directory to path to import base classes
CUR_DIR = Path(__file__).resolve().parent

# Import from local base.py
from base import BaseCollector, BaseNormalize, BaseRun

# Load environment variables
load_dotenv()


class GateCollector(BaseCollector):
    """Gate.io数据采集器，支持日线数据采集"""

    # 交易对列表
    SUPPORTED_PAIRS = ["ETH_USDT", "BTC_USDT"]

    def __init__(
        self,
        save_dir: [str, Path],
        start=None,
        end=None,
        interval="1d",
        max_workers=1,
        max_collector_count=2,
        delay=0.2,  # Gate.io API 建议延迟
        check_data_length: int = None,
        limit_nums: int = None,
    ):
        """
        初始化 Gate.io 数据采集器

        Parameters
        ----------
        save_dir: str
            数据保存目录
        start: str
            开始日期，默认 2024-01-01
        end: str
            结束日期，默认当前日期
        interval: str
            频率，支持 1d（日线）
        max_workers: int
            并发数，默认 1
        max_collector_count: int
            最大采集次数，默认 2
        delay: float
            请求延迟（秒），默认 0.2
        check_data_length: int
            检查数据长度
        limit_nums: int
            限制交易对数量（调试用）
        """
        super(GateCollector, self).__init__(
            save_dir=save_dir,
            start=start,
            end=end,
            interval=interval,
            max_workers=max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )

        # 设置日期时间属性
        self.start_datetime = pd.Timestamp(start) if start else pd.Timestamp.now() - pd.Timedelta(days=365)
        self.end_datetime = pd.Timestamp(end) if end else pd.Timestamp.now()

        # 初始化 Gate.io API 客户端
        self._init_api_client()

        logger.info(f"Gate.io Collector initialized")
        logger.info(f"Start: {self.start_datetime}, End: {self.end_datetime}")
        logger.info(f"Interval: {self.interval}")

    def download_data(self):
        """实现BaseCollector的抽象方法"""
        self.collector_data()

    def collector_data(self):
        """采集数据主流程"""
        logger.info("Starting data collection...")
        logger.info(f"Target directory: {self.save_dir}")
        logger.info(f"Symbols: {self.SUPPORTED_PAIRS}")

        for symbol in self.SUPPORTED_PAIRS:
            logger.info(f"Collecting data for {symbol}")
            try:
                # 获取数据
                df = self.get_data(symbol, self.interval, self.start_datetime, self.end_datetime)

                if df.empty:
                    logger.warning(f"No data collected for {symbol}")
                    continue

                # 保存数据
                output_file = self.save_dir / f"{symbol}.csv"
                df.to_csv(output_file, index=False)
                logger.info(f"Saved {len(df)} rows to {output_file}")

            except Exception as e:
                logger.error(f"Error collecting data for {symbol}: {e}")
                continue

    def _init_api_client(self):
        """初始化 Gate.io API 客户端"""
        # API配置（公开API不需要key和secret）
        config = Configuration()
        self.api_client = ApiClient(config)
        self.spot_api = SpotApi(self.api_client)
        logger.info("Gate.io API client initialized (public API mode)")

    def get_instrument_list(self):
        """获取交易对列表"""
        logger.info("Getting instrument list...")
        return self.SUPPORTED_PAIRS

    def normalize_symbol(self, symbol: str):
        """标准化交易对符号

        将 ETH_USDT 转换为 ETHUSDT 格式用于文件名
        """
        return symbol.replace("_", "").upper()

    def get_data(
        self, symbol: str, interval: str, start_datetime: pd.Timestamp, end_datetime: pd.Timestamp
    ) -> pd.DataFrame:
        """从 Gate.io 获取 K线数据

        Parameters
        ----------
        symbol: str
            交易对符号，如 ETH_USDT
        interval: str
            K线间隔，支持 1d
        start_datetime: pd.Timestamp
            开始时间
        end_datetime: pd.Timestamp
            结束时间

        Returns
        -------
        pd.DataFrame
            包含 date, open, high, low, close, volume 列的数据框
        """
        logger.info(f"Fetching data for {symbol} from {start_datetime} to {end_datetime}")

        try:
            # 转换时间为时间戳（秒）
            start_ts = int(start_datetime.timestamp())
            end_ts = int(end_datetime.timestamp())

            # Gate.io K线间隔映射
            interval_map = {
                "1d": "1d",
                self.INTERVAL_1d: "1d",
            }

            gate_interval = interval_map.get(interval, "1d")

            # 调用 Gate.io API 获取K线数据
            # GET /spot/candlesticks
            # currency_pair, from, to, limit, interval
            logger.info(f"Calling Gate.io API: pair={symbol}, interval={gate_interval}, from={start_ts}, to={end_ts}")

            candlesticks = self.spot_api.list_candlesticks(
                currency_pair=symbol,
                _from=start_ts,
                to=end_ts,
                interval=gate_interval,
                limit=1000  # 每次最多获取1000条
            )

            if not candlesticks:
                logger.warning(f"No data returned for {symbol}")
                return pd.DataFrame()

            # 解析K线数据
            data_list = []
            for candle in candlesticks:
                # Gate.io K线数据格式: [timestamp(str), volume(str), close(str), high(str), low(str), open(str), ...]
                data_list.append({
                    'date': pd.to_datetime(int(candle[0]), unit='s', utc=True).tz_convert('Asia/Shanghai').tz_localize(None),
                    'volume': float(candle[1]),
                    'close': float(candle[2]),
                    'high': float(candle[3]),
                    'low': float(candle[4]),
                    'open': float(candle[5]),
                })

            df = pd.DataFrame(data_list)

            # 确保按日期排序
            df = df.sort_values('date').reset_index(drop=True)

            # 只保留日期部分（去除时间）
            df['date'] = df['date'].dt.date

            # 去重（如果有的话）
            df = df.drop_duplicates(subset=['date'], keep='first')

            # 添加 symbol 列
            df['symbol'] = self.normalize_symbol(symbol)

            logger.info(f"Successfully fetched {len(df)} records for {symbol}")

            return df[['symbol', 'date', 'open', 'high', 'low', 'close', 'volume']]

        except Exception as e:
            logger.error(f"Error fetching data for {symbol}: {e}")
            return pd.DataFrame()


class GateNormalize(BaseNormalize):
    """Gate.io 数据标准化类"""

    def _get_calendar_list(self):
        """获取交易日历列表

        加密货币市场 7x24 小时交易，所以返回 None
        """
        return None

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化数据

        Parameters
        ----------
        df: pd.DataFrame
            原始数据

        Returns
        -------
        pd.DataFrame
            标准化后的数据
        """
        if df.empty:
            return df

        df = df.copy()

        # 确保日期列是 datetime 类型
        df[self._date_field_name] = pd.to_datetime(df[self._date_field_name])

        # 设置日期为索引
        df.set_index(self._date_field_name, inplace=True)

        # 移除重复的日期
        df = df[~df.index.duplicated(keep='first')]

        # 按日期排序
        df.sort_index(inplace=True)

        # 重置索引
        df.index.names = [self._date_field_name]
        df = df.reset_index()

        return df


class Run(BaseRun):
    """Gate.io 数据采集运行类"""

    def __init__(self, source_dir=None, normalize_dir=None, max_workers=1, interval="1d"):
        """
        初始化运行器

        Parameters
        ----------
        source_dir: str
            原始数据保存目录
        normalize_dir: str
            标准化数据保存目录
        max_workers: int
            并发数，默认 1
        interval: str
            频率，默认 1d
        """
        super().__init__(source_dir, normalize_dir, max_workers, interval)

    @property
    def collector_class_name(self):
        return "GateCollector"

    @property
    def normalize_class_name(self):
        return "GateNormalize"

    @property
    def default_base_dir(self) -> [Path, str]:
        return CUR_DIR

    def download_data(
        self,
        max_collector_count=2,
        delay=0.2,
        start="2024-01-01",
        end="2025-10-12",
        check_data_length: int = None,
        limit_nums=None,
    ):
        """下载数据

        Parameters
        ----------
        max_collector_count: int
            最大采集次数，默认 2
        delay: float
            请求延迟（秒），默认 0.2
        start: str
            开始日期，默认 2024-01-01
        end: str
            结束日期，默认 2025-10-12
        check_data_length: int
            检查数据长度
        limit_nums: int
            限制交易对数量（调试用）

        Examples
        --------
            # 下载日线数据
            $ python gate_collector.py download_data --source_dir ./data/gate/source --start 2024-01-01 --end 2025-10-12
        """
        # 确保源目录存在
        if self.source_dir is None:
            self.source_dir = Path(self.default_base_dir).joinpath("source")
        source_dir = Path(self.source_dir).expanduser().resolve()
        source_dir.mkdir(parents=True, exist_ok=True)

        # 创建collector实例并采集数据
        collector = GateCollector(
            save_dir=source_dir,
            max_workers=self.max_workers,
            max_collector_count=max_collector_count,
            delay=delay,
            start=start,
            end=end,
            interval=self.interval,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )
        collector.collector_data()

    def normalize_data(
        self,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
    ):
        """标准化数据

        Parameters
        ----------
        date_field_name: str
            日期字段名，默认 date
        symbol_field_name: str
            交易对字段名，默认 symbol

        Examples
        --------
            $ python gate_collector.py normalize_data --source_dir ./data/gate/source --normalize_dir ./data/gate/normalize
        """
        # 确保源目录和目标目录存在
        if self.source_dir is None:
            self.source_dir = Path(self.default_base_dir).joinpath("source")
        if self.normalize_dir is None:
            self.normalize_dir = Path(self.default_base_dir).joinpath("normalize")

        source_dir = Path(self.source_dir).expanduser().resolve()
        normalize_dir = Path(self.normalize_dir).expanduser().resolve()
        normalize_dir.mkdir(parents=True, exist_ok=True)

        # 创建normalize实例并标准化数据
        normalizer = GateNormalize(
            source_dir=str(source_dir),
            normalize_dir=str(normalize_dir),
        )

        # 遍历源目录中的所有CSV文件
        import glob
        csv_files = glob.glob(str(source_dir / "*.csv"))

        for csv_file in csv_files:
            logger.info(f"Normalizing {csv_file}")
            df = pd.read_csv(csv_file)
            normalized_df = normalizer.normalize(df)

            # 保存标准化后的数据
            output_file = normalize_dir / Path(csv_file).name
            normalized_df.to_csv(output_file, index=False)
            logger.info(f"Saved to {output_file}")


if __name__ == "__main__":
    # 设置模块名为 collector（为了 BaseRun 能正确导入）
    sys.modules['collector'] = sys.modules[__name__]
    fire.Fire(Run)

