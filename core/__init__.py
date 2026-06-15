# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - core 包"""

from .constants import (
    SEARCH_API, DETAIL_API, GREET_API, INTERVIEW_URL, RESUME_BASEINFO_URL, USER_INFO_URL,
    API_HEADERS,
    CITY_CODES, SALARY_CODES, EXP_CODES, DEGREE_CODES,
    INDUSTRY_CODES, SCALE_CODES, STAGE_CODES, JOB_TYPE_CODES,
)
from .parsers import JobSummary, JobDetail, extract_job_summary, extract_job_detail
from .browser import BrowserManager
from .logger import setup_logger
from .base import BaseMixin
from .util import (
    clean_text, extract_skills, build_job_url,
    resolve_code, resolve_city, make_key,
)

__all__ = [
    "SEARCH_API", "DETAIL_API", "GREET_API", "INTERVIEW_URL", "RESUME_BASEINFO_URL", "USER_INFO_URL",
    "API_HEADERS",
    "CITY_CODES", "SALARY_CODES", "EXP_CODES", "DEGREE_CODES",
    "INDUSTRY_CODES", "SCALE_CODES", "STAGE_CODES", "JOB_TYPE_CODES",
    "JobSummary", "JobDetail",
    "extract_job_summary", "extract_job_detail",
    "BrowserManager",
    "setup_logger",
    "clean_text", "extract_skills", "build_job_url",
    "resolve_code", "resolve_city", "make_key",
]
