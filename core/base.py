# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 基础 Mixin（_emit, _save, _request, login, refresh_session）"""

import json
import logging
import time
from pathlib import Path

import httpx

logger = logging.getLogger(__name__)


class BaseMixin:
    """提供 _emit、_save、_request 及统一的登录/刷新/错误处理。"""

    _browser = None         # type: BrowserManager
    _on_message = None
    _save_results = True
    _output_dir = ""

    # ═══════════════════════════════════════════════════════════════════
    #  公开方法 — login / refresh_session
    # ═══════════════════════════════════════════════════════════════════

    def login(self) -> bool:
        """跳转到登录页面，等待用户手动登录。成功返回 True，超时返回 False。"""
        logger.info("请在浏览器中手动登录 Boss直聘...")
        self._browser.tab.get("https://www.zhipin.com/web/user/")
        return self._browser.wait_for_login()

    def refresh_session(self) -> bool:
        """刷新 session：
        1. 导航到 geek/job 刷新页面上下文
        2. 验证 Cookie 是否仍有效
        3. 无效则调用 login() 重新登录
        成功返回 True，最终失败返回 False。
        """
        logger.info("刷新 session...")
        self._browser.refresh_page()
        if self._browser.verify_cookies():
            logger.info("刷新后 Cookie 有效")
            return True
        logger.info("刷新后 Cookie 无效，需要重新登录")
        return self.login()

    # ═══════════════════════════════════════════════════════════════════
    #  内部工具 — _emit, _save, _ok, _is_login_expired_msg
    # ═══════════════════════════════════════════════════════════════════

    def _emit(self, type: str, message: str) -> None:
        logger.info(message)
        if self._on_message:
            try:
                self._on_message({"type": type, "message": message})
            except Exception:
                pass

    def _save(self, data: dict, prefix: str) -> None:
        try:
            output_dir = Path(self._output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = output_dir / f"{prefix}_{ts}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("结果已保存: %s (%d条)", path, len(data))
        except Exception as exc:
            logger.warning("保存失败: %s", exc)

    @staticmethod
    def _ok(data: dict | None) -> bool:
        """判断 API 返回是否成功（data 非 None 且 code==0）。"""
        return data is not None and data.get("code") == 0

    @staticmethod
    def _is_login_expired_msg(message: str) -> bool:
        if not message:
            return False
        return ("登录" in message and ("失效" in message or "过期" in message or "超时" in message)) \
            or "请登录" in message \
            or "身份" in message

    # ═══════════════════════════════════════════════════════════════════
    #  核心 — _request（统一错误处理）
    # ═══════════════════════════════════════════════════════════════════

    def _request(self, url: str, params: dict, referer: str) -> dict | None:
        """统一 HTTP GET 请求。

        自动处理三条分支：
        - code == 0  → 成功，直接返回 data
        - code == 37 → 调用 refresh_session() 后重试一次
        - message 含登录失效关键词 → 调用 login() 后重试一次
        - 其他 code != 0 → 返回 data 供调用方自行处理
        - 网络异常      → 重试一次后返回 None

        调用方统一用 self._ok(data) 判断是否成功。
        """
        cookies, headers = self._browser.build_headers(referer)

        for attempt in range(2):
            try:
                resp = httpx.get(url, params=params, cookies=cookies, headers=headers, timeout=15)
                data = resp.json()
                code = data.get("code", -1)

                # ── 成功 ──
                if code == 0:
                    return data

                msg = data.get("message", "")

                # ── code=37 → 刷新 session ──
                if code == 37:
                    if attempt == 0:
                        logger.info("code=37，触发 refresh_session")
                        if not self.refresh_session():
                            logger.error("refresh_session 失败")
                            return None
                        cookies, headers = self._browser.build_headers(referer)
                        continue
                    logger.error("code=37 重试后仍失败")
                    return None

                # ── 登录失效 → 重新登录 ──
                if self._is_login_expired_msg(msg):
                    if attempt == 0:
                        logger.info("检测到登录失效，触发 login")
                        if not self.login():
                            logger.error("重新登录失败")
                            return None
                        cookies, headers = self._browser.build_headers(referer)
                        continue
                    logger.error("重新登录后重试仍失败")
                    return None

                # ── 其他业务错误 → 返回 data，调用方处理 ──
                return data

            except Exception as exc:
                if attempt == 0:
                    time.sleep(3)
                    continue
                logger.error("请求失败: %s", exc)
                return None

        return None

    def close(self) -> None:
        self._browser.close()
