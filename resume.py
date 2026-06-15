# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 简历模块"""

from .core.constants import RESUME_BASEINFO_URL


class ResumeMixin:
    """简历相关方法。"""

    def get_resume(self) -> dict:
        result = {"baseinfo": {}, "expect": {}}

        data = self._request(RESUME_BASEINFO_URL, {}, "https://www.zhipin.com/web/geek/resume")

        if not self._ok(data):
            msg = data.get("message", "请求失败") if data else "请求失败"
            self._emit("error", f"获取简历基本信息失败: {msg}")
        else:
            result["baseinfo"] = data.get("zpData", {})
            self._emit("progress", "获取简历成功")

        return result
