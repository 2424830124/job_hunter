# -*- coding: utf-8 -*-

import json
import time
import logging

from .assets import *
from .core import BaseMixin

_logger = logging.getLogger(__name__)


class ChatMixin(BaseMixin):
    _my_user_id: int | None = None

    def get_chat_list(self) -> list[dict]:
        """获取全部会话列表。

        Returns:
            [{security_id, name, company, title, last_msg, last_time, last_sender(me/boss), unreplied}, ...]
        """
        raw = self._get_raw_chats()
        if not raw: _logger.warning("获取会话列表成功: 0 条"); return []

        my_id = self._get_my_user_id()
        result = []
        for c in raw:
            info = c.get("lastMessageInfo", {}) or {}
            if isinstance(info, str):
                try:
                    info = json.loads(info)
                except Exception:
                    info = {}
            from_id = info.get("fromId", 0)
            result.append({
                "security_id":    c.get("securityId", ""),
                "name":           c.get("name", ""),
                "company":        c.get("brandName", ""),
                "title":          c.get("title", ""),
                "last_msg":       c.get("lastMsg") or "",
                "last_time":      c.get("lastTime") or "",
                "last_sender":    "me" if from_id == my_id else "boss",
                "unreplied":      from_id != my_id and my_id != 0,
            })
        _logger.info(f"获取会话列表成功: {len(result)} 条")
        return result

    def _get_raw_chats(self) -> list[dict]:
        tab = self._browser.tab
        for attempt in range(2):
            tab.listen.start("getGeekFriendList")
            tab.get("https://www.zhipin.com/web/geek/chat")
            packet = tab.listen.wait(timeout=10)
            tab.listen.stop()
            if packet:
                body = packet.response.body
                if isinstance(body, (str, bytes)): body = json.loads(body)
                result = body.get("zpData", {}).get("result", body.get("result", []))
                if result: return result
            if attempt == 0:
                time.sleep(3)
        return []

    def _get_my_user_id(self) -> int:
        if self._my_user_id is not None: return self._my_user_id

        data = self._request(USER_INFO_URL, {}, "https://www.zhipin.com/web/geek/chat")

        if self._ok(data): self._my_user_id = data.get("zpData", {}).get("userId", 0)
        else: self._my_user_id = 0

        return self._my_user_id



class ContactMixin(BaseMixin):
    def contact(self, security_id: str, lid: str = "") -> str | None:
        """打招呼 / 开始沟通。

        Args:
            security_id: 安全ID
            lid:         追踪参数（可选）

        Returns:
            "succeed" 表示成功，否则返回失败原因（如"开聊提醒"），None 表示网络异常
        """
        params = {"securityId": security_id}
        if lid:
            params["lid"] = lid

        data = self._request(GREET_API, params, "https://www.zhipin.com/web/geek/job")

        if data is None:
            return "请求失败"

        # 打招呼 API 无标准 code 字段，用 message 判断
        msg = data.get("message", "")
        if msg == "Success" or msg == "success":
            _logger.info("打招呼成功")
            return "succeed"

        _logger.warning(f"打招呼失败: {msg}")
        return msg or "未知错误"


