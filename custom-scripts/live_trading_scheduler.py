#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Live Trading Scheduler
Implements scheduled tasks for data collection, model training, and live trading
"""

import os
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np
from loguru import logger
from datetime import datetime, timedelta
import time
import json
import schedule
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

from live_trading_strategy import LiveTradingStrategy, create_live_trading_strategy
from gate_executor import create_gate_executor
from risk_manager import create_risk_manager
from model_manager import ModelManager


class LiveTradingScheduler:
    """实盘交易调度器"""

    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化调度器

        Parameters
        ----------
        config: Dict[str, Any]
            配置参数
        """
        self.config = config or self._get_default_config()

        # 初始化组件
        self.executor = create_gate_executor()
        self.risk_manager = create_risk_manager()
        self.model_manager = ModelManager()
        self.strategy = None

        # 调度器
        self.scheduler = BlockingScheduler()

        # 状态
        self.is_running = False
        self.jobs = {}
        self.execution_logs = []

        logger.info("LiveTradingScheduler initialized")

    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "trading_enabled": True,
            "data_collection_enabled": True,
            "model_retraining_enabled": True,

            # 数据采集调度
            "data_collection_schedule": {
                "price_data": "0 */6 * * *",  # 每6小时
                "news_data": "0 */2 * * *",   # 每2小时
            },

            # 模型训练调度
            "model_training_schedule": {
                "retrain": "0 1 * * 0",  # 每周日凌晨1点
                "hyperparameter_tuning": "0 3 * * 0",  # 每周日凌晨3点
            },

            # 交易调度
            "trading_schedule": {
                "daily_trading": "0 9 * * 1-5",  # 工作日早上9点
                "risk_check": "0 */4 * * *",     # 每4小时
                "performance_report": "0 18 * * *",  # 每天下午6点
            },

            # 其他配置
            "max_concurrent_jobs": 3,
            "job_timeout": 3600,  # 1小时
            "retry_attempts": 3,
            "retry_delay": 300,  # 5分钟
        }

    def start_scheduler(self) -> Dict[str, Any]:
        """启动调度器"""
        try:
            if self.is_running:
                return {"success": False, "error": "Scheduler is already running"}

            # 添加调度任务
            self._add_scheduled_jobs()

            # 启动调度器
            self.is_running = True
            self._log_execution("SCHEDULER_STARTED", "Scheduler started successfully")

            logger.info("Starting scheduler...")
            self.scheduler.start()

            return {"success": True, "message": "Scheduler started successfully"}

        except Exception as e:
            logger.error(f"Error starting scheduler: {e}")
            return {"success": False, "error": str(e)}

    def stop_scheduler(self) -> Dict[str, Any]:
        """停止调度器"""
        try:
            if not self.is_running:
                return {"success": False, "error": "Scheduler is not running"}

            # 停止调度器
            self.scheduler.shutdown()
            self.is_running = False
            self._log_execution("SCHEDULER_STOPPED", "Scheduler stopped")

            return {"success": True, "message": "Scheduler stopped successfully"}

        except Exception as e:
            logger.error(f"Error stopping scheduler: {e}")
            return {"success": False, "error": str(e)}

    def _add_scheduled_jobs(self):
        """添加调度任务"""
        try:
            # 数据采集任务
            if self.config["data_collection_enabled"]:
                self._add_data_collection_jobs()

            # 模型训练任务
            if self.config["model_retraining_enabled"]:
                self._add_model_training_jobs()

            # 交易任务
            if self.config["trading_enabled"]:
                self._add_trading_jobs()

            logger.info(f"Added {len(self.jobs)} scheduled jobs")

        except Exception as e:
            logger.error(f"Error adding scheduled jobs: {e}")

    def _add_data_collection_jobs(self):
        """添加数据采集任务"""
        try:
            # 价格数据采集
            price_schedule = self.config["data_collection_schedule"]["price_data"]
            self.scheduler.add_job(
                func=self._collect_price_data,
                trigger=CronTrigger.from_crontab(price_schedule),
                id="collect_price_data",
                name="Collect Price Data",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["collect_price_data"] = {
                "schedule": price_schedule,
                "last_run": None,
                "status": "scheduled"
            }

            # 链上数据采集已禁用

            # 新闻数据采集
            news_schedule = self.config["data_collection_schedule"]["news_data"]
            self.scheduler.add_job(
                func=self._collect_news_data,
                trigger=CronTrigger.from_crontab(news_schedule),
                id="collect_news_data",
                name="Collect News Data",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["collect_news_data"] = {
                "schedule": news_schedule,
                "last_run": None,
                "status": "scheduled"
            }

        except Exception as e:
            logger.error(f"Error adding data collection jobs: {e}")

    def _add_model_training_jobs(self):
        """添加模型训练任务"""
        try:
            # 模型重训练
            retrain_schedule = self.config["model_training_schedule"]["retrain"]
            self.scheduler.add_job(
                func=self._retrain_model,
                trigger=CronTrigger.from_crontab(retrain_schedule),
                id="retrain_model",
                name="Retrain Model",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["retrain_model"] = {
                "schedule": retrain_schedule,
                "last_run": None,
                "status": "scheduled"
            }

            # 超参数调优
            tuning_schedule = self.config["model_training_schedule"]["hyperparameter_tuning"]
            self.scheduler.add_job(
                func=self._hyperparameter_tuning,
                trigger=CronTrigger.from_crontab(tuning_schedule),
                id="hyperparameter_tuning",
                name="Hyperparameter Tuning",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["hyperparameter_tuning"] = {
                "schedule": tuning_schedule,
                "last_run": None,
                "status": "scheduled"
            }

        except Exception as e:
            logger.error(f"Error adding model training jobs: {e}")

    def _add_trading_jobs(self):
        """添加交易任务"""
        try:
            # 每日交易
            trading_schedule = self.config["trading_schedule"]["daily_trading"]
            self.scheduler.add_job(
                func=self._daily_trading,
                trigger=CronTrigger.from_crontab(trading_schedule),
                id="daily_trading",
                name="Daily Trading",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["daily_trading"] = {
                "schedule": trading_schedule,
                "last_run": None,
                "status": "scheduled"
            }

            # 风险检查
            risk_check_schedule = self.config["trading_schedule"]["risk_check"]
            self.scheduler.add_job(
                func=self._risk_check,
                trigger=CronTrigger.from_crontab(risk_check_schedule),
                id="risk_check",
                name="Risk Check",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["risk_check"] = {
                "schedule": risk_check_schedule,
                "last_run": None,
                "status": "scheduled"
            }

            # 性能报告
            report_schedule = self.config["trading_schedule"]["performance_report"]
            self.scheduler.add_job(
                func=self._generate_performance_report,
                trigger=CronTrigger.from_crontab(report_schedule),
                id="performance_report",
                name="Performance Report",
                max_instances=1,
                replace_existing=True
            )
            self.jobs["performance_report"] = {
                "schedule": report_schedule,
                "last_run": None,
                "status": "scheduled"
            }

        except Exception as e:
            logger.error(f"Error adding trading jobs: {e}")

    def _collect_price_data(self):
        """采集价格数据"""
        try:
            self._log_execution("DATA_COLLECTION_STARTED", "Starting price data collection")

            # 这里应该调用价格数据采集器
            # 为了简化，使用模拟数据
            logger.info("Collecting price data...")
            time.sleep(5)  # 模拟采集时间

            self._log_execution("DATA_COLLECTION_COMPLETED", "Price data collection completed")
            self.jobs["collect_price_data"]["last_run"] = datetime.now().isoformat()
            self.jobs["collect_price_data"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error collecting price data: {e}")
            self._log_execution("DATA_COLLECTION_FAILED", f"Price data collection failed: {str(e)}")
            self.jobs["collect_price_data"]["status"] = "failed"

    def _collect_onchain_data(self):
        """采集链上数据（已禁用）"""
        logger.warning("链上数据采集功能已被禁用")
        self._log_execution("ONCHAIN_COLLECTION_DISABLED", "On-chain data collection is disabled")

    def _collect_news_data(self):
        """采集新闻数据"""
        try:
            self._log_execution("NEWS_COLLECTION_STARTED", "Starting news data collection")

            # 这里应该调用新闻数据采集器
            logger.info("Collecting news data...")
            time.sleep(8)  # 模拟采集时间

            self._log_execution("NEWS_COLLECTION_COMPLETED", "News data collection completed")
            self.jobs["collect_news_data"]["last_run"] = datetime.now().isoformat()
            self.jobs["collect_news_data"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error collecting news data: {e}")
            self._log_execution("NEWS_COLLECTION_FAILED", f"News data collection failed: {str(e)}")
            self.jobs["collect_news_data"]["status"] = "failed"

    def _retrain_model(self):
        """重训练模型"""
        try:
            self._log_execution("MODEL_RETRAINING_STARTED", "Starting model retraining")

            # 这里应该调用模型训练
            logger.info("Retraining model...")
            time.sleep(30)  # 模拟训练时间

            self._log_execution("MODEL_RETRAINING_COMPLETED", "Model retraining completed")
            self.jobs["retrain_model"]["last_run"] = datetime.now().isoformat()
            self.jobs["retrain_model"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error retraining model: {e}")
            self._log_execution("MODEL_RETRAINING_FAILED", f"Model retraining failed: {str(e)}")
            self.jobs["retrain_model"]["status"] = "failed"

    def _hyperparameter_tuning(self):
        """超参数调优"""
        try:
            self._log_execution("HYPERPARAMETER_TUNING_STARTED", "Starting hyperparameter tuning")

            # 这里应该调用超参数调优
            logger.info("Running hyperparameter tuning...")
            time.sleep(60)  # 模拟调优时间

            self._log_execution("HYPERPARAMETER_TUNING_COMPLETED", "Hyperparameter tuning completed")
            self.jobs["hyperparameter_tuning"]["last_run"] = datetime.now().isoformat()
            self.jobs["hyperparameter_tuning"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error in hyperparameter tuning: {e}")
            self._log_execution("HYPERPARAMETER_TUNING_FAILED", f"Hyperparameter tuning failed: {str(e)}")
            self.jobs["hyperparameter_tuning"]["status"] = "failed"

    def _daily_trading(self):
        """每日交易"""
        try:
            self._log_execution("DAILY_TRADING_STARTED", "Starting daily trading")

            # 初始化策略（如果还没有）
            if self.strategy is None:
                self.strategy = create_live_trading_strategy()

            # 运行交易周期
            result = self.strategy._run_trading_cycle()

            if result["success"]:
                self._log_execution("DAILY_TRADING_COMPLETED", f"Daily trading completed: {result}")
            else:
                self._log_execution("DAILY_TRADING_FAILED", f"Daily trading failed: {result}")

            self.jobs["daily_trading"]["last_run"] = datetime.now().isoformat()
            self.jobs["daily_trading"]["status"] = "completed" if result["success"] else "failed"

        except Exception as e:
            logger.error(f"Error in daily trading: {e}")
            self._log_execution("DAILY_TRADING_FAILED", f"Daily trading failed: {str(e)}")
            self.jobs["daily_trading"]["status"] = "failed"

    def _risk_check(self):
        """风险检查"""
        try:
            self._log_execution("RISK_CHECK_STARTED", "Starting risk check")

            # 获取当前持仓和余额
            positions = self.executor.get_positions()
            balance = self.executor.get_balance()
            portfolio_value = sum(balance.values())

            # 计算风险指标
            risk_metrics = self.risk_manager.calculate_risk_metrics(
                {pos["currency"]: pos for pos in positions},
                portfolio_value
            )

            # 生成风险报告
            risk_report = self.risk_manager.generate_risk_report(risk_metrics)

            # 检查风险告警
            if risk_report["alerts"]:
                for alert in risk_report["alerts"]:
                    self._log_execution("RISK_ALERT", f"Risk alert: {alert['message']}")

            self._log_execution("RISK_CHECK_COMPLETED", "Risk check completed")
            self.jobs["risk_check"]["last_run"] = datetime.now().isoformat()
            self.jobs["risk_check"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error in risk check: {e}")
            self._log_execution("RISK_CHECK_FAILED", f"Risk check failed: {str(e)}")
            self.jobs["risk_check"]["status"] = "failed"

    def _generate_performance_report(self):
        """生成性能报告"""
        try:
            self._log_execution("PERFORMANCE_REPORT_STARTED", "Starting performance report generation")

            # 生成性能报告
            if self.strategy:
                report = self.strategy.get_performance_report()

                # 保存报告
                report_path = f"reports/performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                os.makedirs(os.path.dirname(report_path), exist_ok=True)

                with open(report_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, indent=2, ensure_ascii=False, default=str)

                self._log_execution("PERFORMANCE_REPORT_COMPLETED", f"Performance report saved to {report_path}")
            else:
                self._log_execution("PERFORMANCE_REPORT_SKIPPED", "No strategy available for performance report")

            self.jobs["performance_report"]["last_run"] = datetime.now().isoformat()
            self.jobs["performance_report"]["status"] = "completed"

        except Exception as e:
            logger.error(f"Error generating performance report: {e}")
            self._log_execution("PERFORMANCE_REPORT_FAILED", f"Performance report generation failed: {str(e)}")
            self.jobs["performance_report"]["status"] = "failed"

    def _log_execution(self, event_type: str, message: str):
        """记录执行日志"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "event_type": event_type,
            "message": message
        }

        self.execution_logs.append(log_entry)
        logger.info(f"Scheduler Event [{event_type}]: {message}")

    def get_scheduler_status(self) -> Dict[str, Any]:
        """获取调度器状态"""
        return {
            "is_running": self.is_running,
            "total_jobs": len(self.jobs),
            "jobs": self.jobs,
            "total_logs": len(self.execution_logs),
            "config": self.config
        }

    def get_execution_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取执行日志"""
        return self.execution_logs[-limit:] if limit > 0 else self.execution_logs

    def run_job_manually(self, job_id: str) -> Dict[str, Any]:
        """手动运行任务"""
        try:
            if job_id not in self.jobs:
                return {"success": False, "error": f"Job {job_id} not found"}

            # 运行对应的任务
            if job_id == "collect_price_data":
                self._collect_price_data()
            elif job_id == "collect_onchain_data":
                logger.warning("链上数据采集功能已被禁用")
                return {"success": False, "error": "On-chain data collection is disabled"}
            elif job_id == "collect_news_data":
                self._collect_news_data()
            elif job_id == "retrain_model":
                self._retrain_model()
            elif job_id == "hyperparameter_tuning":
                self._hyperparameter_tuning()
            elif job_id == "daily_trading":
                self._daily_trading()
            elif job_id == "risk_check":
                self._risk_check()
            elif job_id == "performance_report":
                self._generate_performance_report()
            else:
                return {"success": False, "error": f"Unknown job: {job_id}"}

            return {"success": True, "message": f"Job {job_id} executed successfully"}

        except Exception as e:
            logger.error(f"Error running job {job_id}: {e}")
            return {"success": False, "error": str(e)}

    def update_config(self, new_config: Dict[str, Any]) -> Dict[str, Any]:
        """更新配置"""
        try:
            # 更新配置
            self.config.update(new_config)

            # 如果调度器正在运行，需要重新添加任务
            if self.is_running:
                self.scheduler.shutdown()
                self._add_scheduled_jobs()
                self.scheduler.start()

            return {"success": True, "message": "Configuration updated successfully"}

        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return {"success": False, "error": str(e)}


def create_live_trading_scheduler(config: Dict[str, Any] = None) -> LiveTradingScheduler:
    """创建实盘交易调度器

    Parameters
    ----------
    config: Dict[str, Any]
        配置参数

    Returns
    -------
    LiveTradingScheduler
        调度器实例
    """
    return LiveTradingScheduler(config=config)


if __name__ == "__main__":
    # 测试调度器
    scheduler = create_live_trading_scheduler()

    # 获取调度器状态
    status = scheduler.get_scheduler_status()
    print(f"Scheduler Status: {status}")

    # 手动运行一个任务进行测试
    result = scheduler.run_job_manually("risk_check")
    print(f"Manual Job Result: {result}")

    # 获取执行日志
    logs = scheduler.get_execution_logs(10)
    print(f"Execution Logs: {logs}")

    # 注意：实际使用时需要调用 scheduler.start_scheduler() 来启动调度器
    # 这会阻塞主线程，所以这里不执行

