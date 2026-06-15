# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 搜索模块"""

import logging
import random
import time
from urllib.parse import quote

from .core.constants import (
    SEARCH_API, SALARY_CODES, EXP_CODES, DEGREE_CODES,
    INDUSTRY_CODES, SCALE_CODES, STAGE_CODES, JOB_TYPE_CODES,
)
from .core.parsers import JobSummary, extract_job_summary
from .core.util import resolve_code, resolve_city, make_key

logger = logging.getLogger(__name__)


class SearchMixin:
    """搜索相关方法。"""

    def search(
        self,
        keyword: str,
        city: str = "101010100",
        count: int = 15,
        salary: str | None = None,
        experience: str | None = None,
        degree: str | None = None,
        industry: str | None = None,
        scale: str | None = None,
        stage: str | None = None,
        job_type: str | None = None,
    ) -> dict:
        # ── 构建参数 ──
        params = {"query": keyword, "city": resolve_city(city), "page": 1, "pageSize": 15}
        for key, val in [
            ("salary", resolve_code(salary, SALARY_CODES)),
            ("experience", resolve_code(experience, EXP_CODES)),
            ("degree", resolve_code(degree, DEGREE_CODES)),
            ("industry", resolve_code(industry, INDUSTRY_CODES)),
            ("scale", resolve_code(scale, SCALE_CODES)),
            ("stage", resolve_code(stage, STAGE_CODES)),
            ("jobType", resolve_code(job_type, JOB_TYPE_CODES)),
        ]:
            if val:
                params[key] = val

        collected: dict[str, JobSummary] = {}
        pages_needed = max(1, -(-count // 15))

        logger.info("========== 开始关键词搜索: %s ==========", keyword)
        for page in range(1, pages_needed + 1):
            params["page"] = page
            data = self._request(
                SEARCH_API, params,
                f"https://www.zhipin.com/web/geek/job?query={quote(keyword)}",
            )

            # ── 统一的 code 判断 ──
            if not self._ok(data):
                if data is None:
                    logger.warning("第 %d 页请求失败，跳过", page)
                else:
                    msg = data.get("message", "未知错误")
                    logger.warning("第 %d 页返回异常: %s", page, msg)
                    if "验证" in str(msg) or "频繁" in str(msg):
                        self._emit("error", f"搜索被拦截: {msg}")
                        break
                continue

            try:
                job_list = data.get("zpData", {}).get("jobList", [])
            except Exception as e:
                logger.warning("第 %d 页解析异常: %s", page, e)
                continue

            if not job_list:
                break

            for raw in job_list:
                job = extract_job_summary(raw)
                if job and job.job_id and job.job_id not in collected:
                    collected[job.job_id] = job

            logger.info("第 %d 页: 新增 %d 个岗位", page, len(job_list))
            if len(collected) >= count:
                break
            time.sleep(random.uniform(0.5, 1.5))

        self._emit("progress", f"搜索完成: {keyword} → {len(collected)} 个岗位")

        result = self._jobs_to_dict(list(collected.values())[:count])
        if self._save_results and result:
            self._save(result, prefix="search")
        return result

    # ── 内部 ──────────────────────────────────────────────────────────

    def _jobs_to_dict(self, jobs: list[JobSummary]) -> dict:
        result: dict = {}
        seen: dict = {}
        for job in jobs:
            key = make_key(job.job_name, job.job_id, seen)
            result[key] = self._summary_to_api_dict(job)
        return result

    @staticmethod
    def _summary_to_api_dict(job: JobSummary) -> dict:
        return {
            "security_id": job.security_id or job.job_id,
            "encrypt_id": job.job_id,
            "degree": job.education,
            "experience": job.experience,
            "skills": list(job.skills),
            "salary": job.salary,
            "city": job.city,
            "company": job.company_name,
            "size": job.company_size,
            "financing": job.company_stage or "",
            "industry": job.company_industry,
            "dialogue": bool(job.raw_data.get("contact", False)),
            "boss_name": job.boss_name,
            "boss_id": job.boss_id,
            "area_district": job.area_district,
            "business_district": job.business_district,
            "job_labels": list(job.job_labels),
            "welfare_list": list(job.welfare_list),
        }
