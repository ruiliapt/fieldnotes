"""
日志模块 - 统一日志管理
"""
import os
import glob
import logging
from datetime import datetime, timedelta
from logging.handlers import RotatingFileHandler


def setup_logger() -> logging.Logger:
    """
    配置并返回应用程序根日志记录器

    - 日志目录: ~/.fieldnote/logs/
    - 文件名: fieldnote_YYYY-MM-DD.log
    - 文件级别: DEBUG, 控制台级别: WARNING
    - 单文件最大 5MB, RotatingFileHandler
    - 自动清理 30 天前的日志
    """
    log_dir = os.path.join(os.path.expanduser("~"), ".fieldnote", "logs")
    os.makedirs(log_dir, exist_ok=True)

    # 清理旧日志
    _cleanup_old_logs(log_dir, max_days=30)

    # 日志文件路径
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = os.path.join(log_dir, f"fieldnote_{today}.log")

    # 获取根 logger
    logger = logging.getLogger("fieldnote")
    logger.setLevel(logging.DEBUG)

    # 避免重复添加 handler
    if logger.handlers:
        return logger

    # 日志格式
    fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    # 文件 handler: DEBUG 级别, 单文件最大 5MB, 保留 3 个备份
    file_handler = RotatingFileHandler(
        log_file, maxBytes=5 * 1024 * 1024, backupCount=3, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(fmt)
    logger.addHandler(file_handler)

    # 控制台 handler: WARNING 级别
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(fmt)
    logger.addHandler(console_handler)

    logger.info("日志系统已初始化, 日志文件: %s", log_file)
    return logger


def _cleanup_old_logs(log_dir: str, max_days: int = 30):
    """清理超过 max_days 天的日志文件"""
    cutoff = datetime.now() - timedelta(days=max_days)
    pattern = os.path.join(log_dir, "fieldnote_*.log*")

    for filepath in glob.glob(pattern):
        try:
            mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
            if mtime < cutoff:
                os.remove(filepath)
        except OSError:
            pass
