# -*- coding: utf-8 -*-

import logging
import time
import atexit
import signal
import httpx

from DrissionPage import ChromiumPage, ChromiumOptions

from ..assets import STEALTH_JS
from ..assets import API_HEADERS, USER_INFO_URL


_logger = logging.getLogger(__name__)
LOGIN_COOKIE = "__zp_stoken__"
LOGIN_TIMEOUT = 300

class BrowserManager:
    def __init__(self, browser_path: str, user_data_dir: str):
        self._browser_path = browser_path
        self._user_data_dir = user_data_dir
        self._page: ChromiumPage | None = None

        atexit.register(self.close)
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def start(self):
        _logger.info("启动浏览器...")
        co = ChromiumOptions()
        co.set_browser_path(self._browser_path)
        co.set_local_port(9222)
        co.set_user_data_path(str(self._user_data_dir))
        co.set_argument('https://www.zhipin.com/')
        for arg in [
            "--disable-blink-features=AutomationControlled",
            "--disable-infobars", "--no-first-run",
            "--disable-extensions", "--disable-popup-blocking",
            "--disable-default-apps", "--disable-gpu",
            "--window-size=900,900",
        ]:
            co.set_argument(arg)

        self._page = ChromiumPage(addr_or_opts=co)
        time.sleep(5)
        self._inject_stealth()
        return self._page

    def verify_cookies(self) -> bool:
        try:
            cookies, headers = self.build_headers()
            resp = httpx.get(USER_INFO_URL, cookies=cookies, headers=headers, timeout=10)
            data = resp.json()
            return data.get("code") == 0
        except Exception: return False

    def login(self) -> bool:
        _logger.info("请在浏览器中手动登录 Boss直聘...")
        try:
            if "www.zhipin.com/web/user/" not in self.tab.url:
                self.tab.get("https://www.zhipin.com/web/user/")
                time.sleep(2)
        except Exception: pass

        deadline = time.monotonic() + LOGIN_TIMEOUT
        while time.monotonic() < deadline:
            if self.verify_cookies(): _logger.info("登录成功"); return True
            time.sleep(1)
        _logger.error("登录超时")
        return False

    def refresh_page(self):
        _logger.info("刷新浏览器页面...")
        self.tab.get(self.tab.url)
        time.sleep(2)

    # ──────────────────────────────────────────────────────

    @property
    def tab(self):
        return self._page.latest_tab

    def _inject_stealth(self):
        try:
            self.tab.run_js(STEALTH_JS)
        except Exception as e:
            _logger.warning("反检测脚本注入失败: %s", e)

    def get_cookies_dict(self) -> dict[str, str]:
        try: return {c.get("name", ""): c.get("value", "") for c in self.tab.cookies()}
        except Exception: return {}

    def build_headers(self, referer: str = "") -> tuple[dict[str, str], dict[str, str]]:
        cookies = self.get_cookies_dict()
        headers = dict(API_HEADERS)
        if referer: headers["Referer"] = referer
        bst = cookies.get("bst", "")
        if bst: headers["zp_token"] = bst
        return cookies, headers

    def close(self):
        if self._page:
            try: self._page.quit()
            except Exception: pass
            self._page = None

    def signal_handler(self, sig, frame):
        self.close()