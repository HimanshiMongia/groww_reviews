"""
Groww Weekly Pulse - Scheduler
Runs the full pipeline (Phase 1 -> 4) every Monday at 1:00 PM IST.
All output is logged to logs/scheduler.log.

Usage:
    py scheduler.py                # Start the scheduler (runs in foreground)
    py scheduler.py --run-now      # Run the pipeline immediately, then start scheduler
    py scheduler.py --day monday   # Change the weekly day (default: monday)

Keep this script running in the background (e.g., via Task Scheduler on Windows,
screen/tmux on Linux, or as a system service).
"""

import os
import sys
import time
import logging
import subprocess
import argparse
import schedule
from datetime import datetime

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

def setup_logging():
    """Configure logging to both file and console."""
    os.makedirs(LOGS_DIR, exist_ok=True)
    
    log_file = os.path.join(LOGS_DIR, 'scheduler.log')
    
    logger = logging.getLogger('GrowwPulseScheduler')
    logger.setLevel(logging.INFO)
    
    # File handler - logs everything to scheduler.log
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_format = logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    file_handler.setFormatter(file_format)
    
    # Console handler - also prints to terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_format = logging.Formatter('[%(asctime)s] %(message)s', datefmt='%H:%M:%S')
    console_handler.setFormatter(console_format)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logging()

def run_pipeline():
    """Execute the full CLI pipeline (Phase 1-4) via pulse.py."""
    logger.info("=" * 60)
    logger.info("SCHEDULED RUN: Starting Weekly Pulse Pipeline...")
    logger.info("=" * 60)
    
    pulse_script = os.path.join(PROJECT_ROOT, 'pulse.py')
    
    try:
        result = subprocess.run(
            [sys.executable, pulse_script],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=1800  # 30-minute timeout for the entire pipeline
        )
        
        # Log stdout line by line
        if result.stdout:
            for line in result.stdout.strip().splitlines():
                logger.info(f"[PIPELINE] {line}")
        
        # Log stderr (warnings, errors)
        if result.stderr:
            for line in result.stderr.strip().splitlines():
                logger.warning(f"[STDERR] {line}")
        
        if result.returncode == 0:
            logger.info("Pipeline completed successfully!")
        else:
            logger.error(f"Pipeline exited with code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logger.error("Pipeline timed out after 30 minutes.")
    except Exception as e:
        logger.error(f"Failed to run pipeline: {e}")


def main():
    parser = argparse.ArgumentParser(description="Groww Weekly Pulse - Scheduler")
    parser.add_argument('--run-now', action='store_true', help='Run the pipeline immediately before starting the scheduler')
    parser.add_argument('--day', type=str, default='monday', 
                        choices=['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
                        help='Day of the week to run the pipeline (default: monday)')
    args = parser.parse_args()
    
    # Schedule the job based on the chosen day
    run_time = "13:00"  # 1:00 PM IST
    
    day_map = {
        'monday': schedule.every().monday,
        'tuesday': schedule.every().tuesday,
        'wednesday': schedule.every().wednesday,
        'thursday': schedule.every().thursday,
        'friday': schedule.every().friday,
        'saturday': schedule.every().saturday,
        'sunday': schedule.every().sunday,
    }
    
    day_map[args.day].at(run_time).do(run_pipeline)
    
    logger.info("=" * 60)
    logger.info("   GROWW WEEKLY PULSE SCHEDULER")
    logger.info("=" * 60)
    logger.info(f"   Scheduled: Every {args.day.capitalize()} at {run_time} IST")
    logger.info(f"   Pipeline:  {os.path.join(PROJECT_ROOT, 'pulse.py')}")
    logger.info(f"   Log file:  {os.path.join(LOGS_DIR, 'scheduler.log')}")
    logger.info("=" * 60)
    logger.info("Scheduler is running. Press Ctrl+C to stop.")
    
    # Run immediately if --run-now flag is set
    if args.run_now:
        logger.info("--run-now flag detected. Running pipeline immediately...")
        run_pipeline()
    
    # Keep the scheduler alive
    try:
        while True:
            schedule.run_pending()
            time.sleep(60)  # Check every 60 seconds
    except KeyboardInterrupt:
        logger.info("Scheduler stopped by user.")


if __name__ == "__main__":
    main()
