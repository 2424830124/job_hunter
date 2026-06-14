"""
job_hunter/_core — 底层实现包，统一对外导出。
"""

from .config import (
    BrowserConfig,
    SearchConfig,
    DetailConfig,
    HumanBehaviorConfig,
    OutputConfig,
    BossConfig,
    BOSS_CONFIG,
    CITY_CODES,
    SALARY_CODES,
    EXP_CODES,
    DEGREE_CODES,
    INDUSTRY_CODES,
    SCALE_CODES,
    STAGE_CODES,
    JOB_TYPE_CODES,
    PROJECT_ROOT,
)
from .browser import BrowserManager
from .parsers import (
    JobSummary,
    JobDetail,
    decode_body,
    extract_skills,
    build_job_url,
    clean_text,
    extract_job_summary,
    extract_job_detail_from_api,
    job_summary_to_api_dict,
    job_detail_to_api_dict,
)
from .logger import setup_logger
from .human import HumanSimulator

__all__ = [
    # config
    "BrowserConfig",
    "SearchConfig",
    "DetailConfig",
    "HumanBehaviorConfig",
    "OutputConfig",
    "BossConfig",
    "BOSS_CONFIG",
    "CITY_CODES",
    "SALARY_CODES",
    "EXP_CODES",
    "DEGREE_CODES",
    "INDUSTRY_CODES",
    "SCALE_CODES",
    "STAGE_CODES",
    "JOB_TYPE_CODES",
    "PROJECT_ROOT",
    # browser
    "BrowserManager",
    # parsers
    "JobSummary",
    "JobDetail",
    "decode_body",
    "extract_skills",
    "build_job_url",
    "clean_text",
    "extract_job_summary",
    "extract_job_detail_from_api",
    "job_summary_to_api_dict",
    "job_detail_to_api_dict",
    # logger
    "setup_logger",
    # human
    "HumanSimulator",
]
