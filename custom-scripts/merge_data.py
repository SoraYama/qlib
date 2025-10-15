#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Merger for Qlib
Merges price data and news sentiment data (on-chain data removed)
"""

import sys
import os
from pathlib import Path
import pandas as pd
import numpy as np
from loguru import logger
import fire

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))


class DataMerger:
    """数据融合器，合并价格和新闻数据（链上数据已移除）"""

    def __init__(self, qlib_data_dir="~/.qlib/qlib_data/crypto_data"):
        """
        初始化数据融合器

        Parameters
        ----------
        qlib_data_dir: str
            Qlib 数据目录路径
        """
        self.qlib_data_dir = Path(qlib_data_dir).expanduser()
        self.data_dir = CUR_DIR.parent / "data"

        logger.info(f"DataMerger initialized")
        logger.info(f"Qlib data dir: {self.qlib_data_dir}")
        logger.info(f"Source data dir: {self.data_dir}")

    def merge_all_data(self, start_date="2024-01-01", end_date="2025-10-12"):
        """合并所有数据源

        Parameters
        ----------
        start_date: str
            开始日期
        end_date: str
            结束日期
        """
        logger.info(f"Merging data from {start_date} to {end_date}")

        # 1. 读取价格数据（已存在的 Qlib 数据）
        price_data = self._load_price_data()
        logger.info(f"Loaded price data: {price_data.shape}")

        # 2. 读取新闻数据（链上数据已移除）
        news_data = self._load_news_data()
        logger.info(f"Loaded news data: {news_data.shape}")

        # 3. 合并数据
        merged_data = self._merge_data_sources(price_data, news_data)
        logger.info(f"Merged data shape: {merged_data.shape}")

        # 5. 保存合并后的数据
        self._save_merged_data(merged_data)

        # 6. 转换为 Qlib 格式
        self._convert_to_qlib_format()

        logger.info("Data merging completed successfully")

    def _load_price_data(self):
        """加载价格数据（从 Qlib 格式）"""
        try:
            import qlib
            from qlib.data import D

            # 初始化 Qlib
            qlib.init(provider_uri=str(self.qlib_data_dir), region="cn")

            # 获取价格数据
            instruments = ["btcusdt", "ethusdt"]
            fields = ["$open", "$high", "$low", "$close", "$volume", "$vwap"]

            data = D.features(
                instruments=instruments,
                fields=fields,
                start_time="2024-01-01",
                end_time="2025-10-12",
                freq="day"
            )

            # 转换为 DataFrame
            df = data.reset_index()
            df.columns = ["instrument", "date", "open", "high", "low", "close", "volume", "vwap"]
            df["symbol"] = df["instrument"].str.upper()
            df = df.drop("instrument", axis=1)

            return df

        except Exception as e:
            logger.error(f"Error loading price data: {e}")
            return pd.DataFrame()


    def _load_news_data(self):
        """加载新闻数据"""
        news_dir = self.data_dir / "news" / "normalize"

        if not news_dir.exists():
            logger.warning(f"News data directory not found: {news_dir}")
            return pd.DataFrame()

        all_data = []

        for file_path in news_dir.glob("*.csv"):
            try:
                df = pd.read_csv(file_path)
                df["date"] = pd.to_datetime(df["date"]).dt.date
                all_data.append(df)
                logger.info(f"Loaded news data from {file_path.name}: {df.shape}")
            except Exception as e:
                logger.error(f"Error loading {file_path}: {e}")

        if all_data:
            return pd.concat(all_data, ignore_index=True)
        else:
            return pd.DataFrame()

    def _merge_data_sources(self, price_data, news_data):
        """合并数据源（链上数据已移除）"""
        if price_data.empty:
            logger.error("No price data available")
            return pd.DataFrame()

        # 以价格数据为基准
        merged_data = price_data.copy()

        # 合并新闻数据
        if not news_data.empty:
            merged_data = merged_data.merge(
                news_data,
                on=["symbol", "date"],
                how="left"
            )
            logger.info("Merged news data")
        else:
            logger.warning("No news data to merge")
            # 添加空的新闻数据列
            news_columns = ["sentiment_score", "news_volume", "weighted_sentiment"]
            for col in news_columns:
                merged_data[col] = np.nan

        # 处理缺失值
        merged_data = self._handle_missing_values(merged_data)

        # 按日期和交易对排序
        merged_data = merged_data.sort_values(["date", "symbol"]).reset_index(drop=True)

        return merged_data

    def _handle_missing_values(self, df):
        """处理缺失值"""
        logger.info("Handling missing values...")

        # 对于链上数据，使用前向填充
        onchain_columns = ["onchain_volume", "active_addresses", "exchange_netflow", "mvrv_ratio"]
        for col in onchain_columns:
            if col in df.columns:
                df[col] = df.groupby("symbol")[col].fillna(method="ffill")

        # 对于新闻数据，使用前向填充
        news_columns = ["sentiment_score", "news_volume", "weighted_sentiment"]
        for col in news_columns:
            if col in df.columns:
                df[col] = df.groupby("symbol")[col].fillna(method="ffill")

        # 对于仍然缺失的值，使用默认值
        default_values = {
            "onchain_volume": 0,
            "active_addresses": 0,
            "exchange_netflow": 0,
            "mvrv_ratio": 1.0,
            "sentiment_score": 0.0,
            "news_volume": 0,
            "weighted_sentiment": 0.0,
        }

        for col, default_val in default_values.items():
            if col in df.columns:
                df[col] = df[col].fillna(default_val)

        logger.info("Missing values handled")
        return df

    def _save_merged_data(self, df):
        """保存合并后的数据"""
        output_dir = self.data_dir / "merged"
        output_dir.mkdir(parents=True, exist_ok=True)

        # 按交易对分别保存
        for symbol in df["symbol"].unique():
            symbol_data = df[df["symbol"] == symbol].copy()
            symbol_data = symbol_data.drop("symbol", axis=1)

            output_file = output_dir / f"{symbol.lower()}.csv"
            symbol_data.to_csv(output_file, index=False)
            logger.info(f"Saved merged data for {symbol}: {symbol_data.shape}")

        # 保存汇总数据
        summary_file = output_dir / "summary.csv"
        df.to_csv(summary_file, index=False)
        logger.info(f"Saved summary data: {df.shape}")

    def _convert_to_qlib_format(self):
        """转换为 Qlib 格式"""
        logger.info("Converting to Qlib format...")

        merged_dir = self.data_dir / "merged"

        if not merged_dir.exists():
            logger.error("Merged data directory not found")
            return

        # 使用 Qlib 的 dump_bin 脚本
        import subprocess

        cmd = [
            "python",
            str(CUR_DIR.parent / "scripts" / "dump_bin.py"),
            "dump_all",
            "--data_path", str(merged_dir),
            "--qlib_dir", str(self.qlib_data_dir),
            "--include_fields", "open,close,high,low,volume,vwap,onchain_volume,active_addresses,exchange_netflow,mvrv_ratio,sentiment_score,news_volume,weighted_sentiment",
            "--symbol_field_name", "symbol",
            "--date_field_name", "date",
            "--freq", "day"
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=CUR_DIR.parent)
            if result.returncode == 0:
                logger.info("Successfully converted to Qlib format")
            else:
                logger.error(f"Error converting to Qlib format: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running dump_bin: {e}")

    def generate_mock_data(self, start_date="2024-01-01", end_date="2025-10-12"):
        """生成模拟数据（用于测试）"""
        logger.info("Generating mock data...")

        # 生成日期范围
        date_range = pd.date_range(start=start_date, end=end_date, freq="D")
        symbols = ["BTCUSDT", "ETHUSDT"]

        all_data = []

        for symbol in symbols:
            for date in date_range:
                # 模拟价格数据
                base_price = 50000 if symbol == "BTCUSDT" else 3000
                price_change = np.random.normal(0, 0.02)  # 2% 日波动
                close_price = base_price * (1 + price_change)

                # 模拟链上数据
                onchain_volume = np.random.lognormal(15, 0.5)
                active_addresses = np.random.lognormal(12, 0.3)
                exchange_netflow = np.random.normal(0, 1000)
                mvrv_ratio = np.random.lognormal(0, 0.3)

                # 模拟新闻数据
                sentiment_score = np.random.normal(0, 0.3)
                news_volume = np.random.poisson(5)
                weighted_sentiment = sentiment_score * (1 + np.random.normal(0, 0.1))

                all_data.append({
                    "symbol": symbol,
                    "date": date.date(),
                    "open": close_price * (1 + np.random.normal(0, 0.01)),
                    "high": close_price * (1 + abs(np.random.normal(0, 0.02))),
                    "low": close_price * (1 - abs(np.random.normal(0, 0.02))),
                    "close": close_price,
                    "volume": np.random.lognormal(20, 0.5),
                    "vwap": close_price * (1 + np.random.normal(0, 0.005)),
                    "onchain_volume": onchain_volume,
                    "active_addresses": active_addresses,
                    "exchange_netflow": exchange_netflow,
                    "mvrv_ratio": mvrv_ratio,
                    "sentiment_score": sentiment_score,
                    "news_volume": news_volume,
                    "weighted_sentiment": weighted_sentiment,
                })

        df = pd.DataFrame(all_data)

        # 保存模拟数据
        self._save_merged_data(df)

        # 转换为 Qlib 格式
        self._convert_to_qlib_format()

        logger.info("Mock data generation completed")


def main():
    """主函数"""
    merger = DataMerger()

    # 检查是否有真实数据
    price_data = merger._load_price_data()
    onchain_data = merger._load_onchain_data()
    news_data = merger._load_news_data()

    if price_data.empty:
        logger.warning("No price data found, generating mock data...")
        merger.generate_mock_data()
    else:
        logger.info("Found price data, merging with available sources...")
        merger.merge_all_data()


if __name__ == "__main__":
    fire.Fire(DataMerger)

