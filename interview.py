# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 面试邀请模块"""

from .core.constants import INTERVIEW_URL


class InterviewMixin:
    """面试邀请相关方法。"""

    def get_interviews(self) -> list[dict]:
        data = self._request(INTERVIEW_URL, {}, "https://www.zhipin.com/web/geek/interview")

        if not self._ok(data):
            msg = data.get("message", "请求失败") if data else "请求失败"
            self._emit("error", f"获取面试邀请失败: {msg}")
            return []

        zp_data = data.get("zpData", {})
        result = zp_data if isinstance(zp_data, list) else zp_data.get("data", [])
        self._emit("progress", f"获取面试邀请成功: {len(result)} 条")
        return result
