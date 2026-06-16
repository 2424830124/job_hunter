# -*- coding: utf-8 -*-

import logging
import time
import httpx

from .browser import BrowserManager

_logger = logging.getLogger(__name__)


class BaseMixin:

    _browser = None         # type: BrowserManager
    _on_message = None
    _output_dir = ""

    def login(self) -> bool:
        """等待用户手动登录。返回 True/False。"""
        return self._browser.login()

    def refresh_session(self) -> bool:
        self._browser.refresh_page()
        if self._browser.verify_cookies():
            return True
        _logger.info("登录状态失效，请重新登录")
        return self.login()

    @staticmethod
    def _ok(data: dict | None) -> bool:
        return data is not None and data.get("code") == 0

    @staticmethod
    def _is_login_expired_msg(message: str) -> bool:
        if not message:
            return False
        return \
            "登录" in message \
        and ("失效" in message or "过期" in message or "超时" in message)\
        or "请登录" in message \
        or "身份" in message

    def _request(self, url: str, params: dict, referer: str) -> dict | None:
        cookies, headers = self._browser.build_headers(referer)

        for attempt in range(2):
            try:
                try: resp = httpx.get(url, params=params, cookies=cookies, headers=headers, timeout=15)
                except Exception as e: _logger.error("连接异常: %s", e); return None

                data = resp.json()
                code = data.get("code", -1)

                if self._ok(data): return data

                # else
                msg = data.get("message", "")
                if attempt: _logger.error("请求异常: %s", msg); return None
                _logger.info("请求异常，正在重试...")

                if code == 37:
                    if not self.refresh_session(): return None
                    cookies, headers = self._browser.build_headers(referer)
                    continue

                if self._is_login_expired_msg(msg):
                    if not self.login(): return None
                    cookies, headers = self._browser.build_headers(referer)
                    continue

                if "验证" in str(msg) or "频繁" in str(msg):
                    _logger.error("请求被拦截: %s", msg)
                    return None

            except Exception as exc:
                if not attempt: time.sleep(3); continue
                _logger.error("请求失败: %s", exc)
                return None

        return None

    def close(self) -> None:
        """断开浏览器连接。"""
        self._browser.close()
