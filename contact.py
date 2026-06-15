# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 打招呼模块"""

from .core.constants import GREET_API


class ContactMixin:
    """打招呼（联系 HR）相关方法。"""

    def contact(self, security_id: str, lid: str = "") -> str:
        params = {"securityId": security_id}
        if lid:
            params["lid"] = lid

        data = self._request(GREET_API, params, "https://www.zhipin.com/web/geek/job")

        if not self._ok(data):
            msg = data.get("message", "请求失败") if data else "请求失败"
            self._emit("error", f"打招呼失败: {msg}")
            return msg

        self._emit("progress", "打招呼成功")
        return "succeed"
