# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 数据结构与解析"""

import logging
import time
from dataclasses import dataclass, field, asdict

from .util import clean_text, extract_skills, build_job_url

logger = logging.getLogger(__name__)


@dataclass
class JobSummary:
    job_id: str = ""
    job_name: str = ""
    salary: str = ""
    city: str = ""
    experience: str = ""
    education: str = ""
    company_name: str = ""
    company_size: str = ""
    company_stage: str = ""
    company_industry: str = ""
    skills: list[str] = field(default_factory=list)
    boss_name: str = ""
    boss_title: str = ""
    boss_id: str = ""
    area_district: str = ""
    business_district: str = ""
    job_labels: list[str] = field(default_factory=list)
    welfare_list: list[str] = field(default_factory=list)
    contact: bool = False
    lid: str = ""
    job_url: str = ""
    security_id: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_data", None)
        return d


@dataclass
class JobDetail:
    job_id: str = ""
    job_name: str = ""
    salary: str = ""
    city: str = ""
    district: str = ""
    experience: str = ""
    education: str = ""
    job_type: str = ""
    skills: list[str] = field(default_factory=list)
    job_description: str = ""
    company_name: str = ""
    company_size: str = ""
    company_stage: str = ""
    company_industry: str = ""
    company_description: str = ""
    boss_name: str = ""
    boss_title: str = ""
    boss_id: str = ""
    boss_avatar: str = ""
    recruitment_count: str = ""
    position_name: str = ""
    job_status: str = ""
    pay_type: str = ""
    work_address: str = ""
    job_url: str = ""
    security_id: str = ""
    fetched_at: str = ""
    raw_data: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("raw_data", None)
        return d


def extract_job_summary(raw: dict) -> JobSummary | None:
    try:
        job_id = str(raw.get("encryptJobId", raw.get("jobId", "")))
        if not job_id:
            return None
        return JobSummary(
            job_id=job_id,
            job_name=clean_text(raw.get("jobName", "")),
            salary=clean_text(raw.get("salaryDesc", "")),
            city=raw.get("cityName", ""),
            experience=raw.get("jobExperience", ""),
            education=raw.get("jobDegree", ""),
            company_name=raw.get("brandName", ""),
            company_size=raw.get("brandScaleName", ""),
            company_stage=raw.get("brandStageName", ""),
            company_industry=raw.get("brandIndustry", ""),
            skills=extract_skills(raw),
            boss_name=raw.get("bossName", ""),
            boss_title=raw.get("bossTitle", ""),
            boss_id=raw.get("bossId", "") or raw.get("encryptBossId", "") or raw.get("bossUserId", ""),
            area_district=raw.get("areaDistrict", ""),
            business_district=raw.get("businessDistrict", ""),
            job_labels=raw.get("jobLabels", []),
            welfare_list=raw.get("welfareList", []),
            contact=bool(raw.get("contact", False)),
            lid=raw.get("lid", ""),
            security_id=raw.get("securityId", ""),
            job_url=build_job_url(job_id),
            raw_data=raw,
        )
    except Exception as e:
        logger.debug("提取摘要失败: %s", e)
        return None


def extract_job_detail(data: dict, job_id: str, detail_url: str) -> JobDetail | None:
    if not data:
        return None
    try:
        zp = data.get("zpData", {})
        job_info = zp.get("jobInfo", {}) or {}
        brand = zp.get("brandComInfo", {}) or {}
        boss = zp.get("bossInfo", {}) or {}

        return JobDetail(
            job_id=job_info.get("encryptId", "") or job_id,
            security_id=zp.get("securityId", ""),
            job_name=clean_text(job_info.get("jobName", "") or zp.get("jobName", "")),
            salary=clean_text(job_info.get("salaryDesc", "") or zp.get("salaryDesc", "")),
            city=job_info.get("locationName", "") or zp.get("cityName", ""),
            district=zp.get("areaDistrict", ""),
            experience=job_info.get("experienceName", "") or zp.get("jobExperience", ""),
            education=job_info.get("degreeName", "") or zp.get("jobDegree", ""),
            job_type=job_info.get("jobType", "") or zp.get("jobType", ""),
            skills=extract_skills(job_info.get("showSkills", []) or zp.get("skills", [])),
            job_description=(
                job_info.get("postDescription", "")
                or zp.get("jobDesc", "")
                or zp.get("postDescription", "")
                or zp.get("jobDetail", "")
                or zp.get("description", "")
                or zp.get("postContent", "")
            ),
            company_name=brand.get("brandName", "") or zp.get("brandName", ""),
            company_size=brand.get("scaleName", "") or zp.get("brandScaleName", ""),
            company_stage=brand.get("stageName", "") or zp.get("brandStageName", ""),
            company_industry=brand.get("industryName", "") or zp.get("brandIndustry", ""),
            company_description=brand.get("introduce", "") or zp.get("brandComDesc", ""),
            boss_name=boss.get("name", "") or zp.get("bossName", ""),
            boss_title=boss.get("title", "") or zp.get("bossTitle", ""),
            boss_id=boss.get("encryptId", "") or zp.get("bossId", "") or zp.get("encryptBossId", ""),
            boss_avatar=zp.get("bossAvatar", ""),
            work_address=job_info.get("address", "") or zp.get("encryptAddress", "") or zp.get("officeAddress", ""),
            recruitment_count=job_info.get("recruitmentCountDesc") or "",
            position_name=job_info.get("positionName") or "",
            job_status=job_info.get("jobStatusDesc") or "",
            pay_type=job_info.get("payTypeDesc") or "",
            job_url=detail_url,
            fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            raw_data=zp,
        )
    except Exception as e:
        logger.error("详情解析失败: %s", e)
        return None
