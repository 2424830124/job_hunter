# -*- coding: utf-8 -*-

import logging
from urllib.parse import quote

from .assets import *
from .core import BaseMixin

_logger = logging.getLogger(__name__)


class SearchMixin(BaseMixin):
    def search(
        self,
        keyword: str,
        city: str = "101010100",
        page: int = 1,
        pagesize: int = 15,
        salary: str | None = None,
        experience: str | None = None,
        degree: str | None = None,
        industry: str | None = None,
        scale: str | None = None,
        stage: str | None = None,
        job_type: str | None = None,
    ) -> list[dict] | None:
        """关键词搜索岗位。

        Args:
            keyword:    搜索关键词
            city:       城市名或编码（如"杭州"、"101210100"），默认全国
            page:       页码
            pagesize:   每页条数
            salary:     薪资筛选（如"20-30K"）
            experience: 经验筛选（如"3-5年"）
            degree:     学历筛选（如"本科"）
            industry:   行业筛选（如"互联网"）
            scale:      规模筛选（如"1000-9999人"）
            stage:      融资阶段（如"B轮"）
            job_type:   岗位类型（"全职"/"实习"/"兼职"）

        Returns:
            [{security_id, encrypt_id, salary, company, ...}] 或 None
        """

        params = {"query": keyword, "city": resolve_city(city), "page": page, "pageSize": pagesize}
        for key, val in [
            ("salary", resolve_code(salary, SALARY_CODES)),
            ("experience", resolve_code(experience, EXP_CODES)),
            ("degree", resolve_code(degree, DEGREE_CODES)),
            ("industry", resolve_code(industry, INDUSTRY_CODES)),
            ("scale", resolve_code(scale, SCALE_CODES)),
            ("stage", resolve_code(stage, STAGE_CODES)),
            ("jobType", resolve_code(job_type, JOB_TYPE_CODES)),
        ]:
            if val: params[key] = val

        collected: [JobSummary] = []

        _logger.info("开始搜索 关键词: %s 第 %d 页", keyword, page)

        params["page"] = page
        data = self._request(
            SEARCH_API, params,
            f"https://www.zhipin.com/web/geek/job?query={quote(keyword)}",
        )

        if data is None: return None
        try: job_list = data.get("zpData", {}).get("jobList", [])
        except Exception as e:
            _logger.warning("解析异常: %s", page, e)
            return None

        if not job_list: return None

        for raw in job_list: collected.append(extract_job_summary(raw))

        result = self._deduplication(collected)
        _logger.info(f"搜索到 {len(result)} 个岗位")

        return result

    def _deduplication(self, jobs: list[JobSummary]) -> list[dict]:
        result: dict = {}
        for job in jobs:
            result[job.security_id] = self._summary_to_api_dict(job)
        return list(result.values())

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



class DetailMixin(BaseMixin):
    def fetch_detail(self, security_id: str, encrypt_job_id: str = "") -> dict | None:
        """查看岗位完整详情。

        Args:
            security_id:    安全ID
            encrypt_job_id: 加密岗位ID（可选）

        Returns:
            {job, detail, salary, company, skills, ...} 或 None
        """
        data = self._request(
            DETAIL_API, {"securityId": security_id},
            "https://www.zhipin.com/web/geek/job",
        )

        if not self._ok(data): return None

        detail_url = build_job_url(encrypt_job_id)
        detail = extract_job_detail(data, encrypt_job_id, detail_url)

        if not detail.job_description:
            _logger.warning(f"详情为空 (id={security_id})")
            return None

        _logger.info(f"获取详情成功: {detail.job_name}")
        return self._detail_to_api_dict(detail)

    @staticmethod
    def _detail_to_api_dict(job: JobDetail) -> dict:
        return {
            "job": job.job_name,
            "security_id": job.security_id or job.job_id,
            "encrypt_id": job.job_id,
            "detail": job.job_description,
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
            "address": job.work_address,
            "recruitment_count": job.recruitment_count,
            "position_name": job.position_name,
            "job_status": job.job_status,
            "pay_type": job.pay_type,
        }