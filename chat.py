# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 会话列表模块"""

import json
import time

from .core.constants import USER_INFO_URL


class ChatMixin:
    """会话列表相关方法。"""

    _my_user_id: int | None = None

    def get_chat_list(self) -> list[dict]:
        raw = self._get_raw_chats()
        if not raw:
            self._emit("progress", "获取会话列表成功: 0 条")
            return []

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
                "uid": c.get("uid", 0),
                "name": c.get("name", ""),
                "company": c.get("brandName", ""),
                "title": c.get("title", ""),
                "last_msg": c.get("lastMsg") or "",
                "last_time": c.get("lastTime") or "",
                "last_sender": "me" if from_id == my_id else "boss",
                "unread": from_id != my_id and my_id != 0,
            })
        self._emit("progress", f"获取会话列表成功: {len(result)} 条")
        return result

    # ── 内部 ──────────────────────────────────────────────────────────

    def _get_raw_chats(self) -> list[dict]:
        tab = self._browser.tab
        for attempt in range(2):
            tab.listen.start("getGeekFriendList")
            tab.get("https://www.zhipin.com/web/geek/chat")
            packet = tab.listen.wait(timeout=10)
            tab.listen.stop()
            if packet:
                body = packet.response.body
                if isinstance(body, (str, bytes)):
                    body = json.loads(body)
                result = body.get("zpData", {}).get("result", body.get("result", []))
                if result:
                    return result
            if attempt == 0:
                time.sleep(3)
        return []

    def _get_my_user_id(self) -> int:
        if self._my_user_id is not None:
            return self._my_user_id

        data = self._request(USER_INFO_URL, {}, "https://www.zhipin.com/web/geek/chat")

        if self._ok(data):
            self._my_user_id = data.get("zpData", {}).get("userId", 0)
        else:
            self._my_user_id = 0

        return self._my_user_id
