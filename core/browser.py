# -*- coding: utf-8 -*-
"""Boss直聘岗位抓取 SDK - 浏览器管理器"""

import logging
import time

import httpx
from DrissionPage import ChromiumPage, ChromiumOptions

from .constants import API_HEADERS, USER_INFO_URL

logger = logging.getLogger(__name__)

STEALTH_JS = r"""
Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
if (!window.chrome) { window.chrome = { runtime: {}, loadTimes: function() {}, csi: function() {}, app: {} }; }
const _orig_toString = Function.prototype.toString;
Function.prototype.toString = function() {
    if (this === Function.prototype.toString) return 'function toString() { [native code] }';
    return _orig_toString.call(this);
};
const _orig_query = window.navigator.permissions?.query;
if (_orig_query) {
    window.navigator.permissions.query = (p) =>
        p.name === 'notifications' ? Promise.resolve({ state: Notification.permission }) : _orig_query(p);
}
Object.defineProperty(navigator, 'plugins', { get: () => [1,2,3,4,5] });
Object.defineProperty(navigator, 'languages', { get: () => ['zh-CN','zh','en-US','en'] });
console.log('[StealthJS] injected OK');
"""


class BrowserManager:
    """浏览器生命周期管理：启动、反检测、Cookie 提取与验证、关闭。"""

    LOGIN_COOKIE = "__zp_stoken__"
    LOGIN_TIMEOUT = 300

    def __init__(self, browser_path: str, user_data_dir: str):
        self._browser_path = browser_path
        self._user_data_dir = user_data_dir
        self._page: ChromiumPage | None = None

    # ── 浏览器生命周期 ────────────────────────────────────────────────

    @property
    def tab(self):
        return self._page.latest_tab

    def start(self):
        """启动浏览器并注入反检测脚本。"""
        logger.info("========== 启动浏览器 ==========")
        co = ChromiumOptions()
        co.set_browser_path(self._browser_path)
        co.set_local_port(9222)
        co.set_user_data_path(str(self._user_data_dir))
        for arg in [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars", "--no-first-run",
            "--disable-extensions", "--disable-popup-blocking",
            "--disable-default-apps", "--disable-gpu",
            "--window-size=1920,1080",
        ]:
            co.set_argument(arg)

        self._page = ChromiumPage(addr_or_opts=co)
        time.sleep(5)
        self._inject_stealth()
        return self._page

    def close(self):
        """关闭浏览器。"""
        if self._page:
            try:
                self._page.quit()
            except Exception:
                pass
            self._page = None

    # ── Cookie / Header ───────────────────────────────────────────────

    def get_cookies_dict(self) -> dict[str, str]:
        """获取当前所有 Cookie 的 dict。"""
        try:
            return {c.get("name", ""): c.get("value", "") for c in self.tab.cookies()}
        except Exception:
            return {}

    def build_headers(self, referer: str = "") -> tuple[dict[str, str], dict[str, str]]:
        """构建请求用的 (cookies_dict, headers_dict)。"""
        cookies = self.get_cookies_dict()
        headers = dict(API_HEADERS)
        if referer:
            headers["Referer"] = referer
        bst = cookies.get("bst", "")
        if bst:
            headers["zp_token"] = bst
        return cookies, headers

    # ── 登录与验证 ────────────────────────────────────────────────────

    def verify_cookies(self) -> bool:
        """用当前 Cookie 调 user/info 接口验证是否有效。"""
        try:
            cookies = self.get_cookies_dict()
            headers = dict(API_HEADERS)
            bst = cookies.get("bst", "")
            if bst:
                headers["zp_token"] = bst
            resp = httpx.get(USER_INFO_URL, cookies=cookies, headers=headers, timeout=10)
            data = resp.json()
            return data.get("code") == 0
        except Exception as e:
            logger.debug("验证 Cookie 失败: %s", e)
            return False

    def wait_for_login(self) -> bool:
        """轮询等待用户手动登录完成（最长 LOGIN_TIMEOUT 秒）。"""
        logger.info("请在浏览器中手动登录 Boss直聘...")
        try:
            if "zhipin.com" not in self.tab.url:
                self.tab.get("https://www.zhipin.com")
                time.sleep(2)
        except Exception:
            pass

        deadline = time.monotonic() + self.LOGIN_TIMEOUT
        while time.monotonic() < deadline:
            if self.verify_cookies():
                logger.info("[OK] 登录成功，Cookie 有效!")
                return True
            time.sleep(2)
        logger.error("[FAIL] 登录超时")
        return False

    def refresh_page(self):
        """导航到 geek/job 页面刷新 session 上下文。"""
        logger.info("刷新浏览器 session 页面...")
        self.tab.get("https://www.zhipin.com/web/geek/job")
        time.sleep(2)

    # ── 内部工具 ──────────────────────────────────────────────────────

    def _inject_stealth(self):
        try:
            self._page.latest_tab.run_js(STEALTH_JS)
        except Exception as e:
            logger.warning("反检测脚本注入失败: %s", e)
