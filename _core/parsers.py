# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 共享解析模块

定义核心数据类 :class:`JobSummary`、:class:`JobDetail`，
以及从 API 响应中提取字段的工具函数。
所有模块共用此处的数据结构，不得在其他模块重复定义。
"""

import json
import logging
import time
from dataclasses import dataclass, field, asdict

logger = logging.getLogger(__name__)


@dataclass
class JobSummary:
    """
    岗位摘要信息（从列表 API 中提取）。

    对应 Boss直聘搜索/推荐接口返回的单条岗位数据，
    ``raw_data`` 字段保留原始 JSON dict，转换为字典时会自动剔除。
    """

    job_id: str = ""                            # encryptJobId
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
        """返回字段字典（不含 ``raw_data``）。"""
        d = asdict(self)
        d.pop("raw_data", None)
        return d


@dataclass
class JobDetail:
    """
    岗位完整详情（从详情 API 或 DOM 中提取）。

    ``raw_data`` 字段保留原始 ``zpData`` dict，转换为字典时会自动剔除。
    """

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
        """返回字段字典（不含 ``raw_data``）。"""
        d = asdict(self)
        d.pop("raw_data", None)
        return d


# ============================================================
# 通用工具
# ============================================================

def decode_body(body: object) -> dict | None:
    """
    将 API 响应体解码为 dict。

    Args:
        body: ``dict``、``bytes`` 或 JSON ``str``。

    Returns:
        解析后的 dict，或 ``None``（无法解析时）。
    """
    if isinstance(body, dict):
        return body
    if isinstance(body, bytes):
        body = body.decode("utf-8", errors="replace")
    if isinstance(body, str):
        try:
            return json.loads(body)
        except (json.JSONDecodeError, ValueError):
            return None
    return None


def extract_skills(raw) -> list[str]:
    """
    从岗位原始 dict 或 list 中提取技能标签列表。

    兼容字符串列表和 ``{"name": ...}`` 对象列表两种格式。
    """
    if isinstance(raw, list):
        src = raw
    elif isinstance(raw, dict):
        src = raw.get("skills", raw.get("showSkills", []))
    else:
        return []
    if isinstance(src, dict):
        src = []
    if not src:
        return []
    skills = []
    for item in src:
        if isinstance(item, str):
            skills.append(item)
        elif isinstance(item, dict):
            name = item.get("name", "")
            if name:
                skills.append(name)
    return skills


def build_job_url(job_id: str) -> str:
    """
    根据 ``encryptJobId`` 构造岗位详情页 URL。

    Args:
        job_id: encryptJobId 字符串。

    Returns:
        完整的 Boss直聘岗位详情页 URL。
    """
    return f"https://www.zhipin.com/job_detail/{job_id}.html"


def clean_text(text: str) -> str:
    """
    清理文本：去除首尾空白，仅保留第一行。

    Args:
        text: 原始文本（可为空字符串）。

    Returns:
        清理后的单行文本。
    """
    if not text:
        return ""
    return text.strip().split("\n")[0].strip()


# ============================================================
# API 响应解析
# ============================================================

def extract_job_summary(raw: dict) -> JobSummary | None:
    """
    将单条岗位原始 dict 解析为 :class:`JobSummary`。

    Args:
        raw: 来自 API ``jobList`` 的单条岗位 dict。

    Returns:
        :class:`JobSummary` 实例，或 ``None``（缺少 ID 时）。
    """
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
        logger.debug("提取失败: %s", e)
        return None


def extract_job_detail_from_api(body: object, job_id: str, detail_url: str) -> JobDetail | None:
    """
    将详情 API 响应解析为 :class:`JobDetail`。

    ``job_description`` 按优先级依次尝试：
    ``jobInfo.postDescription`` → ``zpData.jobDesc`` → ``zpData.postDescription``
    → ``zpData.jobDetail`` → ``zpData.description`` → ``zpData.postContent``。

    Args:
        body:       API 响应体（dict / bytes / str）。
        job_id:     encryptJobId（用于填充 ``job_id`` 兜底）。
        detail_url: 详情页 URL（写入 ``job_url`` 字段）。

    Returns:
        :class:`JobDetail` 实例，或 ``None``（响应为空/解析失败时）。
    """
    data = decode_body(body)
    if not data:
        return None
    try:
        zp = data.get("zpData", {})
        job_info = zp.get("jobInfo", {}) or {}
        brand = zp.get("brandComInfo", {}) or {}
        boss = zp.get("bossInfo", {}) or {}

        result = JobDetail(
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
        if not result.job_description:
            logger.debug("job_description 为空，zpData keys: %s", list(zp.keys()))
        return result
    except Exception as e:
        logger.error("详情解析失败: %s", e)
        return None


# ============================================================
# API 输出转换
# ============================================================

def _financing(company_stage: str) -> str:
    """融资阶段字段透传（预留格式化扩展点）。"""
    return company_stage or ""


def _dialogue_from_raw(raw: dict) -> bool:
    """从原始 dict 中推断是否已沟通。"""
    for key in ("hasCommented", "dialogue", "isCommunicated"):
        val = raw.get(key)
        if val is not None:
            return bool(val)
    return False


def job_summary_to_api_dict(job: "JobSummary") -> dict:
    """
    将 :class:`JobSummary` 转换为对外 API 字典格式。

    Args:
        job: :class:`JobSummary` 实例。

    Returns:
        字段扁平化的 dict，供 :class:`~job_hunter.BossZhipin` 方法返回给调用者。
    """
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
        "financing": _financing(job.company_stage),
        "industry": job.company_industry,
        "dialogue": bool(job.raw_data.get("contact", False)) or _dialogue_from_raw(job.raw_data),
        "boss_name": job.boss_name,
        "boss_id": job.boss_id,
        "area_district": job.area_district,
        "business_district": job.business_district,
        "job_labels": list(job.job_labels),
        "welfare_list": list(job.welfare_list),
    }


def job_detail_to_api_dict(job: "JobDetail") -> dict:
    """
    将 :class:`JobDetail` 转换为对外 API 字典格式。

    Args:
        job: :class:`JobDetail` 实例。

    Returns:
        字段扁平化的 dict，供 :meth:`~job_hunter.BossZhipin.fetch_detail` 返回给调用者。
    """
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
        "financing": _financing(job.company_stage),
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
