#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
News Sentiment Data Collector for Qlib
Collects cryptocurrency news and performs sentiment analysis
"""

import sys
import os
from pathlib import Path
from datetime import datetime, timedelta
import time
import requests
import pandas as pd
import numpy as np
from loguru import logger
from dotenv import load_dotenv

# Add parent directory to path to import base classes
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent / "scripts" / "data_collector"))
from base import BaseCollector, BaseNormalize, BaseRun

# Load environment variables
load_dotenv()


class NewsCollector(BaseCollector):
    """新闻情绪数据采集器，支持 CryptoPanic API"""

    # 支持的交易对和对应的新闻关键词
    SUPPORTED_PAIRS = ["BTCUSDT", "ETHUSDT"]

    # 交易对到新闻关键词的映射
    COIN_KEYWORDS = {
        "BTCUSDT": ["bitcoin", "btc"],
        "ETHUSDT": ["ethereum", "eth"]
    }

    def __init__(
        self,
        save_dir: [str, Path],
        start=None,
        end=None,
        interval="1d",
        max_workers=1,
        max_collector_count=2,
        delay=1.0,  # API 请求延迟
        check_data_length: int = None,
        limit_nums: int = None,
    ):
        """
        初始化新闻数据采集器

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
            请求延迟（秒），默认 1.0
        check_data_length: int
            检查数据长度
        limit_nums: int
            限制交易对数量（调试用）
        """
        super(NewsCollector, self).__init__(
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

        # 初始化 API 配置
        self.cryptopanic_api_key = os.getenv("CRYPTOPANIC_API_KEY")
        self.newsapi_key = os.getenv("NEWSAPI_KEY")

        if not self.cryptopanic_api_key and not self.newsapi_key:
            logger.warning("No news API keys found in environment variables")
            logger.info("Using mock data for development")

        # 初始化情绪分析模型
        self.sentiment_analyzer = None
        self._init_sentiment_analyzer()

        logger.info(f"News Collector initialized")
        logger.info(f"Start: {self.start_datetime}, End: {self.end_datetime}")
        logger.info(f"Interval: {self.interval}")

    def _init_sentiment_analyzer(self):
        """初始化情绪分析模型"""
        try:
            from transformers import pipeline
            logger.info("Loading FinBERT sentiment analysis model...")
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model="ProsusAI/finbert",
                tokenizer="ProsusAI/finbert"
            )
            logger.info("FinBERT model loaded successfully")
        except Exception as e:
            logger.warning(f"Failed to load FinBERT model: {e}")
            logger.info("Will use simple sentiment analysis")
            self.sentiment_analyzer = None

    def get_instrument_list(self):
        """获取交易对列表"""
        logger.info("Getting instrument list...")
        return self.SUPPORTED_PAIRS

    def normalize_symbol(self, symbol: str):
        """标准化交易对符号"""
        return symbol.upper()

    def get_data(
        self, symbol: str, interval: str, start_datetime: pd.Timestamp, end_datetime: pd.Timestamp
    ) -> pd.DataFrame:
        """获取新闻情绪数据

        Parameters
        ----------
        symbol: str
            交易对符号，如 BTCUSDT
        interval: str
            数据间隔，支持 1d
        start_datetime: pd.Timestamp
            开始时间
        end_datetime: pd.Timestamp
            结束时间

        Returns
        -------
        pd.DataFrame
            包含 date, sentiment_score, news_volume, weighted_sentiment 列的数据框
        """
        logger.info(f"Fetching news sentiment data for {symbol} from {start_datetime} to {end_datetime}")

        try:
            # 获取该交易对对应的关键词
            keywords = self.COIN_KEYWORDS.get(symbol, [])
            if not keywords:
                logger.warning(f"No keywords defined for {symbol}")
                return pd.DataFrame()

            # 生成日期范围
            date_range = pd.date_range(start=start_datetime, end=end_datetime, freq="D")

            all_data = []

            for date in date_range:
                logger.info(f"Processing news for {symbol} on {date.date()}")

                # 获取当日新闻
                news_list = self._fetch_daily_news(symbol, keywords, date)

                if not news_list:
                    logger.warning(f"No news found for {symbol} on {date.date()}")
                    # 使用前一日数据或默认值
                    sentiment_score = 0.0
                    news_volume = 0
                    weighted_sentiment = 0.0
                else:
                    # 分析情绪
                    sentiment_score, news_volume, weighted_sentiment = self._analyze_sentiment(news_list)

                all_data.append({
                    "symbol": symbol,
                    "date": date.date(),
                    "sentiment_score": sentiment_score,
                    "news_volume": news_volume,
                    "weighted_sentiment": weighted_sentiment
                })

                # API 限流
                time.sleep(self.delay)

            df = pd.DataFrame(all_data)
            logger.info(f"Successfully fetched {len(df)} records for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Error fetching news data for {symbol}: {e}")
            return pd.DataFrame()

    def _fetch_daily_news(self, symbol: str, keywords: list, date: pd.Timestamp) -> list:
        """获取指定日期的新闻"""
        news_list = []

        # 尝试从 CryptoPanic 获取新闻
        if self.cryptopanic_api_key:
            cryptopanic_news = self._fetch_cryptopanic_news(symbol, keywords, date)
            news_list.extend(cryptopanic_news)

        # 尝试从 NewsAPI 获取新闻
        if self.newsapi_key:
            newsapi_news = self._fetch_newsapi_news(symbol, keywords, date)
            news_list.extend(newsapi_news)

        # 如果没有 API 密钥，生成模拟数据
        if not news_list and not self.cryptopanic_api_key and not self.newsapi_key:
            news_list = self._generate_mock_news(symbol, date)

        return news_list

    def _fetch_cryptopanic_news(self, symbol: str, keywords: list, date: pd.Timestamp) -> list:
        """从 CryptoPanic API 获取新闻"""
        try:
            # 获取日期范围（前后1天）
            start_date = (date - timedelta(days=1)).strftime("%Y-%m-%d")
            end_date = (date + timedelta(days=1)).strftime("%Y-%m-%d")

            url = "https://cryptopanic.com/api/v1/posts/"
            params = {
                "auth_token": self.cryptopanic_api_key,
                "currencies": symbol.replace("USDT", ""),  # BTC, ETH
                "public": "true",
                "filter": "rising",
                "kind": "news"
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            news_list = []

            if "results" in data:
                for item in data["results"]:
                    # 检查日期是否在目标范围内
                    item_date = pd.to_datetime(item["published_at"]).date()
                    if start_date <= item_date.strftime("%Y-%m-%d") <= end_date:
                        news_list.append({
                            "title": item.get("title", ""),
                            "content": item.get("title", ""),  # CryptoPanic 主要提供标题
                            "published_at": item["published_at"],
                            "votes": item.get("votes", {}),
                            "source": "cryptopanic"
                        })

            logger.info(f"Fetched {len(news_list)} news from CryptoPanic for {symbol}")
            return news_list

        except Exception as e:
            logger.error(f"Error fetching CryptoPanic news: {e}")
            return []

    def _fetch_newsapi_news(self, symbol: str, keywords: list, date: pd.Timestamp) -> list:
        """从 NewsAPI 获取新闻"""
        try:
            # 构建搜索查询
            query = " OR ".join(keywords) + " cryptocurrency"

            url = "https://newsapi.org/v2/everything"
            params = {
                "apiKey": self.newsapi_key,
                "q": query,
                "from": date.strftime("%Y-%m-%d"),
                "to": date.strftime("%Y-%m-%d"),
                "language": "en",
                "sortBy": "relevancy",
                "pageSize": 50
            }

            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()

            data = response.json()
            news_list = []

            if "articles" in data:
                for article in data["articles"]:
                    news_list.append({
                        "title": article.get("title", ""),
                        "content": article.get("description", ""),
                        "published_at": article["publishedAt"],
                        "source": "newsapi",
                        "url": article.get("url", "")
                    })

            logger.info(f"Fetched {len(news_list)} news from NewsAPI for {symbol}")
            return news_list

        except Exception as e:
            logger.error(f"Error fetching NewsAPI news: {e}")
            return []

    def _generate_mock_news(self, symbol: str, date: pd.Timestamp) -> list:
        """生成模拟新闻数据（用于开发测试）"""
        logger.info(f"Generating mock news for {symbol} on {date.date()}")

        # 模拟新闻标题和内容
        mock_news_templates = [
            f"{symbol.replace('USDT', '')} price shows strong bullish momentum",
            f"Market analysts predict {symbol.replace('USDT', '')} will reach new highs",
            f"{symbol.replace('USDT', '')} faces resistance at key levels",
            f"Institutional adoption of {symbol.replace('USDT', '')} continues to grow",
            f"Technical indicators suggest {symbol.replace('USDT', '')} may consolidate",
            f"{symbol.replace('USDT', '')} trading volume reaches record levels",
            f"Regulatory concerns weigh on {symbol.replace('USDT', '')} sentiment",
            f"{symbol.replace('USDT', '')} ecosystem shows promising developments"
        ]

        # 随机选择 3-8 条新闻
        num_news = np.random.randint(3, 9)
        selected_news = np.random.choice(mock_news_templates, num_news, replace=False)

        news_list = []
        for title in selected_news:
            news_list.append({
                "title": title,
                "content": title,  # 简化处理
                "published_at": date.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "source": "mock",
                "votes": {"positive": np.random.randint(0, 10), "negative": np.random.randint(0, 5)}
            })

        return news_list

    def _analyze_sentiment(self, news_list: list) -> tuple:
        """分析新闻情绪

        Returns
        -------
        tuple: (sentiment_score, news_volume, weighted_sentiment)
        """
        if not news_list:
            return 0.0, 0, 0.0

        sentiment_scores = []
        weights = []

        for news in news_list:
            # 获取文本内容
            text = news.get("title", "") + " " + news.get("content", "")
            if not text.strip():
                continue

            # 分析情绪
            if self.sentiment_analyzer:
                # 使用 FinBERT 模型
                try:
                    result = self.sentiment_analyzer(text[:512])  # 限制长度
                    if result[0]["label"] == "LABEL_0":  # 负面
                        score = -result[0]["score"]
                    else:  # 正面
                        score = result[0]["score"]
                except Exception as e:
                    logger.warning(f"Sentiment analysis failed: {e}")
                    score = self._simple_sentiment_analysis(text)
            else:
                # 简单情绪分析
                score = self._simple_sentiment_analysis(text)

            # 计算权重（基于投票或新闻来源）
            weight = 1.0
            if "votes" in news:
                positive_votes = news["votes"].get("positive", 0)
                negative_votes = news["votes"].get("negative", 0)
                total_votes = positive_votes + negative_votes
                if total_votes > 0:
                    weight = 1.0 + (total_votes / 10.0)  # 投票越多权重越高

            sentiment_scores.append(score)
            weights.append(weight)

        if not sentiment_scores:
            return 0.0, len(news_list), 0.0

        # 计算加权平均情绪得分
        weighted_sentiment = np.average(sentiment_scores, weights=weights)

        # 计算简单平均情绪得分
        sentiment_score = np.mean(sentiment_scores)

        # 新闻数量
        news_volume = len(news_list)

        return float(sentiment_score), news_volume, float(weighted_sentiment)

    def _simple_sentiment_analysis(self, text: str) -> float:
        """简单情绪分析（基于关键词）"""
        positive_words = [
            "bullish", "rise", "increase", "growth", "positive", "strong",
            "up", "gain", "breakthrough", "adoption", "institutional"
        ]
        negative_words = [
            "bearish", "fall", "decrease", "decline", "negative", "weak",
            "down", "loss", "crash", "regulation", "ban", "concern"
        ]

        text_lower = text.lower()

        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)

        total_words = positive_count + negative_count
        if total_words == 0:
            return 0.0

        # 返回 -1 到 1 之间的得分
        return (positive_count - negative_count) / total_words


class NewsNormalize(BaseNormalize):
    """新闻数据标准化类"""

    def _get_calendar_list(self):
        """获取交易日历列表

        新闻数据也是 7x24 小时，所以返回 None
        """
        return None

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        """标准化新闻数据

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
    """新闻数据采集运行类"""

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
        return "NewsCollector"

    @property
    def normalize_class_name(self):
        return "NewsNormalize"

    @property
    def default_base_dir(self) -> [Path, str]:
        return CUR_DIR

    def download_data(
        self,
        max_collector_count=2,
        delay=1.0,
        start="2024-01-01",
        end="2025-10-12",
        check_data_length: int = None,
        limit_nums=None,
    ):
        """下载新闻数据

        Parameters
        ----------
        max_collector_count: int
            最大采集次数，默认 2
        delay: float
            请求延迟（秒），默认 1.0
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
            # 下载新闻数据
            $ python news_collector.py download_data --source_dir ./data/news/source --start 2024-01-01 --end 2025-10-12
        """
        super(Run, self).download_data(
            max_collector_count=max_collector_count,
            delay=delay,
            start=start,
            end=end,
            check_data_length=check_data_length,
            limit_nums=limit_nums,
        )

    def normalize_data(
        self,
        date_field_name: str = "date",
        symbol_field_name: str = "symbol",
    ):
        """标准化新闻数据

        Parameters
        ----------
        date_field_name: str
            日期字段名，默认 date
        symbol_field_name: str
            交易对字段名，默认 symbol

        Examples
        --------
            $ python news_collector.py normalize_data --source_dir ./data/news/source --normalize_dir ./data/news/normalize
        """
        super(Run, self).normalize_data(
            date_field_name=date_field_name,
            symbol_field_name=symbol_field_name,
        )


if __name__ == "__main__":
    # 设置模块名为 collector（为了 BaseRun 能正确导入）
    sys.modules['collector'] = sys.modules[__name__]
    fire.Fire(Run)

