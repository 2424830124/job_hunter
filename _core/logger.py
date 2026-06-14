# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 日志配置模块
统一管理日志的格式、输出位置、级别等。
"""

import logging
import sys
from pathlib import Path

from .config import BOSS_CONFIG


def setup_logger(
    log_dir: Path | None = None,
    console: bool = True,
    save_log: bool = True,
) -> logging.Logger:
    """
    配置全局日志系统。
    Args:
        log_dir: 日志文件目录
        console: 是否输出到控制台
        save_log: 是否写入日志文件
    """
    _log_dir = Path(log_dir) if isinstance(log_dir, str) else (log_dir or BOSS_CONFIG.output.log_dir)
    _log_dir.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)

    # 清除已有 handler（避免重复注册）
    root_logger.handlers.clear()

    # 格式化器
    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 控制台 handler（直接使用 sys.stdout，由系统编码决定输出）
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG)
        console_handler.setFormatter(fmt)
        root_logger.addHandler(console_handler)

    # 文件 handler
    if save_log:
        log_file = _log_dir / "job_hunter.log"
        file_handler = logging.FileHandler(
            str(log_file), encoding="utf-8", mode="a", errors="replace"
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(fmt)
        root_logger.addHandler(file_handler)
    else:
        log_file = None

    logger = logging.getLogger(__name__)
    logger.info("日志系统已初始化 (文件: %s)", log_file or "(无)")
    return root_logger
