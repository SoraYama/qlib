#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Data Collection Scheduler
Simple scheduler for data collection tasks
"""

import os
import sys
import time
from pathlib import Path
from loguru import logger
from datetime import datetime, timedelta

# Add parent directory to path
CUR_DIR = Path(__file__).resolve().parent
sys.path.append(str(CUR_DIR.parent))

def collect_data():
    """Collect cryptocurrency data"""
    try:
        logger.info("Starting data collection...")

        # Import gate collector
        from gate_collector import GateCollector

        # Initialize collector
        collector = GateCollector(
            save_dir="/app/data/gate/source",
            start=datetime.now() - timedelta(days=1),
            end=datetime.now(),
            delay=0.5
        )

        # Collect data
        collector.download_data()

        logger.info("Data collection completed successfully")

    except Exception as e:
        logger.error(f"Error in data collection: {e}")

def normalize_data():
    """Normalize collected data"""
    try:
        logger.info("Starting data normalization...")

        from gate_collector import GateCollector

        # Normalize data
        collector = GateCollector(
            save_dir="/app/data/gate/source",
            normalize_dir="/app/data/gate/normalize"
        )

        collector.normalize()

        logger.info("Data normalization completed successfully")

    except Exception as e:
        logger.error(f"Error in data normalization: {e}")

def main():
    """Main scheduler function"""
    logger.info("Starting data collection scheduler...")

    # Run initial data collection
    collect_data()
    normalize_data()

    # Simple loop - run every hour
    while True:
        logger.info("Waiting for next data collection cycle...")
        time.sleep(3600)  # Wait 1 hour

        # Run data collection
        collect_data()
        normalize_data()

if __name__ == "__main__":
    main()
