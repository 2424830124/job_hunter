# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 详情模块"""

import logging

from .core.constants import DETAIL_API
from .core.parsers import JobDetail, extract_job_detail
from .core.util import build_job_url

logger = logging.getLogger(__name__)


class DetailMixin:
    """详情相关方法。"""

    def fetch_detail(self, security_id: str, encrypt_job_id: str = "") -> dict:
        try:
            data = self._request(
                DETAIL_API, {"securityId": security_id},
                "https://www.zhipin.com/web/geek/job",
            )

            if not self._ok(data):
                msg = data.get("message", "请求失败") if data else "请求失败"
                self._emit("error", f"获取详情失败: {msg} (id={security_id})")
                return {"error": msg, "id": security_id}

            detail_url = build_job_url(encrypt_job_id)
            detail = extract_job_detail(data, encrypt_job_id, detail_url)
            if detail is None:
                self._emit("error", f"获取详情失败: 解析失败 (id={security_id})")
                return {"error": "解析失败", "id": security_id}
            if not detail.job_description:
                self._emit("error", f"获取详情失败: 详情为空 (id={security_id})")
                return {"error": "详情为空", "id": security_id}

            self._emit("progress", f"获取详情成功: {detail.job_name}")
            return self._detail_to_api_dict(detail)

        except Exception as exc:
            logger.error("fetch_detail 异常: %s", exc)
            self._emit("error", f"获取详情异常: {exc} (id={security_id})")
            return {"error": str(exc), "id": security_id}

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
