"""
Boss直聘岗位抓取系统 - 关键词搜索模块
纯 httpx API 调用，不导航页面。
"""

import logging
import random
import time

import httpx

from ._core.browser import BrowserManager
from ._core.config import SearchConfig, BOSS_CONFIG
from ._core.constants import SEARCH_API
from ._core.parsers import JobSummary, extract_job_summary

logger = logging.getLogger(__name__)


class JobSearcher:
    """关键词搜索模块。纯 API 调用。"""

    def __init__(self, browser: BrowserManager, config: SearchConfig | None = None):
        self._browser = browser
        self._config = config or BOSS_CONFIG.search
        self._collected: dict[str, JobSummary] = {}

    def run(self, max_jobs: int | None = None) -> list[JobSummary]:
        logger.info("========== 开始关键词搜索 ==========")
        pages_needed = 1
        if max_jobs:
            pages_needed = max(1, -(-max_jobs // 15))

        for kw in self._config.keywords:
            city = self._config._resolve_city(self._config.city_code)
            for page in range(1, pages_needed + 1):
                self._search_page(kw, city, page)
                if max_jobs and len(self._collected) >= max_jobs:
                    break
                time.sleep(random.uniform(0.5, 1.5))
            if max_jobs and len(self._collected) >= max_jobs:
                break

        logger.info("搜索完成，共 %d 个去重岗位", len(self._collected))
        return list(self._collected.values())[:max_jobs] if max_jobs else list(self._collected.values())

    def _search_page(self, keyword: str, city: str, page: int) -> None:
        logger.info("搜索: %s (第%d页)", keyword, page)
        cookies, headers = self._browser.build_headers(
            f"https://www.zhipin.com/web/geek/job?query={keyword}"
        )

        # 构建查询参数
        params = {"query": keyword, "city": city, "page": page, "pageSize": 15}
        
        # 添加筛选参数
        _filter_map = [
            ("salary", self._config.salary),
            ("experience", self._config.experience),
            ("degree", self._config.degree),
            ("industry", self._config.industry),
            ("scale", self._config.scale),
            ("stage", self._config.stage),
            ("jobType", self._config.job_type),
        ]
        for key, val in _filter_map:
            if val:
                params[key] = val

        for attempt in range(2):
            try:
                resp = httpx.get(SEARCH_API,
                    params=params,
                    cookies=cookies, headers=headers, timeout=15)
                data = resp.json()

                if data.get("code") == 37:
                    cookies = self._browser.refresh_session()
                    headers["zp_token"] = cookies.get("bst", "")
                    continue

                job_list = data.get("zpData", {}).get("jobList", [])
                if job_list:
                    for raw in job_list:
                        job = extract_job_summary(raw)
                        if job and job.job_id and job.job_id not in self._collected:
                            self._collected[job.job_id] = job
                    logger.info("新增 %d 个岗位", len([j for j in job_list if j.get("encryptJobId")]))
                    return
                if attempt == 0:
                    time.sleep(3)
            except Exception as e:
                if attempt == 0:
                    time.sleep(3)
                else:
                    logger.error("搜索 API 异常: %s", e)
