# -*- coding: utf-8 -*-

import logging

from .assets import *
from .core import BaseMixin

_logger = logging.getLogger(__name__)


class ResumeMixin(BaseMixin):
    def get_resume(self) -> dict | None:
        """获取简历信息。

        Returns:
            {"baseinfo": {...}, "expect": {...}} 或 None
        """
        result = {"baseinfo": {}, "expect": {}}

        data = self._request(RESUME_BASEINFO_URL, {}, "https://www.zhipin.com/web/geek/resume")

        if data is None: return None

        result["baseinfo"] = data.get("zpData", {})
        _logger.info("获取简历成功")

        return result




class InterviewMixin(BaseMixin):
    def get_interviews(self) -> list[dict] | None:
        """获取面试邀请列表。

        Returns:
            [{...}] 或 None
        """
        data = self._request(INTERVIEW_URL, {}, "https://www.zhipin.com/web/geek/interview")

        if data is None: return None

        zp_data = data.get("zpData", {})
        result = zp_data if isinstance(zp_data, list) else zp_data.get("data", [])
        _logger.info(f"获取面试邀请: {len(result)} 条")
        return result