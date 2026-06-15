# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 日志配置"""

import logging
from pathlib import Path


def setup_logger(log_dir: str, console: bool = True, save_log: bool = True) -> None:
    _log_dir = Path(log_dir)
    _log_dir.mkdir(parents=True, exist_ok=True)

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.handlers.clear()

    for lib in ("httpx", "httpcore", "urllib3", "asyncio"):
        logging.getLogger(lib).setLevel(logging.WARNING)

    fmt = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if console:
        import sys
        h = logging.StreamHandler(sys.stdout)
        h.setLevel(logging.DEBUG)
        h.setFormatter(fmt)
        root.addHandler(h)

    if save_log:
        h = logging.FileHandler(str(_log_dir / "job_hunter.log"), encoding="utf-8", mode="a", errors="replace")
        h.setLevel(logging.DEBUG)
        h.setFormatter(fmt)
        root.addHandler(h)
