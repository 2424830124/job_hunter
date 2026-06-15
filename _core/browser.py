# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 浏览器接管与初始化模块

负责启动/连接真实 Edge 浏览器、注入反检测脚本、检测登录状态。
其他模块通过 :class:`BrowserManager` 的 :attr:`~BrowserManager.tab`
属性获取当前活跃标签页，通过 :meth:`~BrowserManager.get_cookies_dict`
获取登录 Cookie。
"""

import logging
import time

from DrissionPage import ChromiumPage, ChromiumOptions

from .config import BrowserConfig, BOSS_CONFIG
from .constants import API_HEADERS

logger = logging.getLogger(__name__)

# ============================================================
# 反检测 JS 注入脚本
# ============================================================
STEALTH_JS: str = """
// 1. 屏蔽 CDP 端口探测 —— 将 navigator.webdriver 设为 undefined
Object.defineProperty(navigator, 'webdriver', {
    get: () => undefined,
});

// 2. 伪造 chrome 对象（部分检测脚本会检查 window.chrome）
if (!window.chrome) {
    window.chrome = {
        runtime: {},
        loadTimes: function() {},
        csi: function() {},
        app: {},
    };
}

// 3. 屏蔽 CDP Runtime.enable 检测
//    重写 Function.prototype.toString，隐藏原生函数被修改的痕迹
const originalToString = Function.prototype.toString;
Function.prototype.toString = function() {
    if (this === Function.prototype.toString) {
        return 'function toString() { [native code] }';
    }
    return originalToString.call(this);
};

// 4. 覆盖 permissions API（某些检测脚本通过 query 来判断自动化）
const originalQuery = window.navigator.permissions?.query;
if (originalQuery) {
    window.navigator.permissions.query = (parameters) => (
        parameters.name === 'notifications' ?
            Promise.resolve({ state: Notification.permission }) :
            originalQuery(parameters)
    );
}

// 5. 覆盖 plugins 长度（无头浏览器通常 plugins 为空）
Object.defineProperty(navigator, 'plugins', {
    get: () => [1, 2, 3, 4, 5],
});

// 6. 覆盖 languages
Object.defineProperty(navigator, 'languages', {
    get: () => ['zh-CN', 'zh', 'en-US', 'en'],
});

console.log('[StealthJS] anti-detect script injected OK');
"""


class BrowserManager:
    """
    浏览器管理器。

    职责：

    1. 通过 :class:`~DrissionPage.ChromiumOptions` 配置并启动/接管真实 Edge 浏览器。
    2. 注入反检测 JS（:data:`STEALTH_JS`）。
    3. 检测用户登录状态（轮询 Cookie）。
    4. 提供统一的 :attr:`tab` 访问入口和 :meth:`get_cookies_dict` 工具。

    Args:
        config: 浏览器配置，默认取 :data:`~.config.BOSS_CONFIG`.browser。
    """

    def __init__(self, config: BrowserConfig | None = None):
        self._config = config or BOSS_CONFIG.browser
        self._page: ChromiumPage | None = None
        logger.info(
            "BrowserManager 配置: port=%d, user_data=%s",
            self._config.remote_debugging_port,
            self._config.user_data_dir,
        )

    # --------------------------------------------------------
    # 公开接口
    # --------------------------------------------------------

    @property
    def page(self) -> ChromiumPage:
        """当前 :class:`~DrissionPage.ChromiumPage` 实例。"""
        if self._page is None:
            raise RuntimeError("浏览器尚未初始化，请先调用 start()")
        return self._page

    @property
    def tab(self):
        """当前活跃标签页（``latest_tab``）。"""
        return self.page.latest_tab

    def start(self) -> ChromiumPage:
        """
        启动浏览器并返回 page 对象。

        流程：创建配置 → 启动浏览器 → 注入反检测脚本。

        Returns:
            已初始化的 :class:`~DrissionPage.ChromiumPage` 实例。
        """
        logger.info("========== 启动浏览器 ==========")
        co = self._build_options()
        logger.info("正在启动 Edge 浏览器...")
        self._page = ChromiumPage(addr_or_opts=co)

        # 等待浏览器完全启动
        time.sleep(5)
        logger.info("浏览器启动成功，正在注入反检测脚本...")
        self._inject_stealth_js()
        logger.info("反检测脚本注入完成")

        return self._page

    def wait_for_login(self) -> bool:
        """
        等待用户手动完成登录。

        通过轮询 :attr:`~.config.BrowserConfig.login_cookie_name` 来判断登录状态。

        Returns:
            ``True`` 表示登录成功，``False`` 表示超时。
        """
        logger.info("请在浏览器中手动登录 Boss直聘...")
        logger.info("等待检测 Cookie: '%s' (最长等待 %ds)",
                    self._config.login_cookie_name, self._config.login_wait_timeout)

        deadline = time.monotonic() + self._config.login_wait_timeout
        check_interval = 2.0

        while time.monotonic() < deadline:
            if self._check_login():
                logger.info("[OK] 登录成功! 检测到 Cookie: '%s'", self._config.login_cookie_name)
                return True
            remaining = deadline - time.monotonic()
            logger.debug("等待登录... 剩余 %.0fs", remaining)
            time.sleep(check_interval)

        logger.error("[FAIL] 登录超时 (%ds), 请重新运行程序", self._config.login_wait_timeout)
        return False

    def close(self) -> None:
        """关闭浏览器连接（不关闭浏览器进程本身，保留登录态）。"""
        if self._page:
            try:
                self._page.quit()
                logger.info("浏览器连接已关闭")
            except Exception as e:
                logger.warning("关闭浏览器时出错: %s", e)
            finally:
                self._page = None

    def ensure_stealth(self) -> None:
        """确保当前页面已注入反检测脚本（导航到新页面后调用）。"""
        try:
            tab = self._page.latest_tab
            tab.run_js(STEALTH_JS)
        except Exception as e:
            logger.debug("重新注入 Stealth JS 失败: %s", e)

    def get_cookies_dict(self) -> dict[str, str]:
        """
        获取当前浏览器所有 Cookie 的 ``name → value`` 字典。

        Returns:
            Cookie 字典，失败时返回空字典。
        """
        try:
            return {c.get("name", ""): c.get("value", "") for c in self.tab.cookies()}
        except Exception:
            return {}

    def build_headers(self, referer: str = "") -> tuple[dict[str, str], dict[str, str]]:
        """
        构建 httpx 请求所需的 cookies 和 headers。

        Args:
            referer: Referer 头

        Returns:
            (cookies_dict, headers_dict)
        """
        cookies = self.get_cookies_dict()
        headers = dict(API_HEADERS)
        if referer:
            headers["Referer"] = referer
        bst = cookies.get("bst", "")
        if bst:
            headers["zp_token"] = bst
        return cookies, headers

    def refresh_session(self) -> dict[str, str]:
        """
        刷新 session（code=37 时）。如果已经登录了就刷新后返回 Cookie；
        如果还没登录就先调用登录方法，等用户登录后再返回 Cookie。
        """
        logger.info("code=37，刷新 session")
        self.tab.get("https://www.zhipin.com/web/geek/job")
        time.sleep(2)

        # 检查是否已登录（不调用 _check_login，避免页面跳转）
        try:
            for cookie in self.tab.cookies():
                if cookie.get("name") == self._config.login_cookie_name:
                    return self.get_cookies_dict()
        except Exception as e:
            logger.debug("Cookie 检测异常: %s", e)

        logger.info("登录失效，请重新登录")
        self.wait_for_login()
        return self.get_cookies_dict()

    # --------------------------------------------------------
    # 内部方法
    # --------------------------------------------------------

    def _build_options(self) -> ChromiumOptions:
        """构建 :class:`~DrissionPage.ChromiumOptions` 配置对象。"""
        co = ChromiumOptions()
        co.set_browser_path(self._config.browser_path)
        co.set_local_port(self._config.remote_debugging_port)

        user_data = str(self._config.user_data_dir)
        co.set_user_data_path(user_data)
        logger.info("用户数据目录: %s", user_data)

        for arg in self._config.arguments:
            co.set_argument(arg)


        if self._config.headless:
            co.headless()

        return co

    def _inject_stealth_js(self) -> None:
        """向当前页面注入反检测 JavaScript（:data:`STEALTH_JS`）。"""
        try:
            tab = self._page.latest_tab
            tab.run_js(STEALTH_JS)
            logger.debug("Stealth JS 已注入")
        except Exception as e:
            logger.warning("反检测脚本注入失败: %s", e)

    def _check_login(self) -> bool:
        """通过检测 Cookie 判断是否已登录。"""
        try:
            tab = self._page.latest_tab
            current_url = tab.url
            if "zhipin.com" not in current_url:
                tab.get("https://www.zhipin.com")
                time.sleep(2)

            cookies = tab.cookies()
            for cookie in cookies:
                if cookie.get("name") == self._config.login_cookie_name:
                    return True
            return False
        except Exception as e:
            logger.debug("Cookie 检测异常: %s", e)
            return False
