# -*- coding: utf-8 -*-

import logging

from .constants import CITY_CODES

_logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    if not text:
        return ""
    return text.strip().split("\n")[0].strip()


def extract_skills(raw) -> list[str]:
    if isinstance(raw, list):
        src = raw
    elif isinstance(raw, dict):
        src = raw.get("skills", raw.get("showSkills", []))
    else:
        return []
    if isinstance(src, dict):
        return []
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
    return f"https://www.zhipin.com/job_detail/{job_id}.html"


def resolve_code(value: str | None, code_dict: dict[str, str]) -> str | None:
    if not value:
        return None
    if value.isdigit():
        return value
    if value in code_dict:
        return code_dict[value]
    _logger.warning("未知的筛选项值: %r", value)
    return value


def resolve_city(city: str) -> str:
    if city.isdigit():
        return city
    return CITY_CODES.get(city, city)

