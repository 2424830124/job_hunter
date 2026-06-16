# -*- coding: utf-8 -*-
"""
job_hunter — Boss直聘岗位抓取 SDK

基于 httpx + 真实浏览器 Cookie，纯 API 调用，高速稳定。

使用示例::

    from job_hunter import BossZhipin

    a = BossZhipin(
        browser_path=r"C:\\...\\msedge.exe",
        user_data_dir=r"./browser_data",
        output_dir=r"./output",
        log_dir=r"./logs",
    )
    jobs = a.search(keyword="Python", city="杭州", count=10)
    detail = a.fetch_detail(security_id="...", encrypt_job_id="...")
    a.contact(security_id="...")
    a.get_chat_list()
    a.close()
"""

from .assets import *
from .core import *
from .core import BossZhipin

__all__ = []
__version__ = "2.0.0"
