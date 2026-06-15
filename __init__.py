# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取 SDK

基于 httpx + 真实浏览器 Cookie，纯 API 调用，高速稳定。

使用示例::

    from job_hunter import BossZhipin

    a = BossZhipin(
        browser_path=r"C:\\...\\msedge.exe",
        user_data_dir=r"./browser_data",
        output_dir=r"./output",
        log_dir=r"./logs",
        on_message=lambda msg: print(msg["message"]),
    )
    jobs = a.search(keyword="Python", city="北京", count=10)
    detail = a.fetch_detail(security_id="...", encrypt_job_id="...")
    ok = a.contact(security_id="...")
    chats = a.get_chat_list()
    a.close()
"""



from .core.base import BaseMixin
from .core.browser import BrowserManager
from .core.logger import setup_logger
from .search import SearchMixin
from .detail import DetailMixin
from .contact import ContactMixin
from .chat import ChatMixin
from .interview import InterviewMixin
from .resume import ResumeMixin
from .core.parsers import JobSummary, JobDetail
from .core.constants import (
    CITY_CODES, SALARY_CODES, EXP_CODES, DEGREE_CODES,
    INDUSTRY_CODES, SCALE_CODES, STAGE_CODES, JOB_TYPE_CODES,
)


class BossZhipin(
    BaseMixin,
    SearchMixin,
    DetailMixin,
    ContactMixin,
    ChatMixin,
    InterviewMixin,
    ResumeMixin,
):
    """Boss直聘 SDK — 自动管理浏览器登录态，统一错误处理。

    __init__ 流程：
        1. 启动浏览器
        2. 尝试用已有 Cookie 验证
        3. 有效 → 直接就绪；无效 → 调用 login() 等待用户登录
    """

    def __init__(
        self,
        browser_path: str,
        user_data_dir: str,
        output_dir: str,
        log_dir: str,
        save_results: bool = True,
        save_log: bool = True,
        console_log: bool = True,
        on_message: callable = None,
    ):
        # ── 参数校验 ──
        for name, val in [
            ("browser_path", browser_path), ("user_data_dir", user_data_dir),
            ("output_dir", output_dir), ("log_dir", log_dir),
        ]:
            if not val:
                raise ValueError(f"{name} 为必填参数")

        self._save_results = save_results
        self._output_dir = output_dir
        self._on_message = on_message

        setup_logger(log_dir=log_dir, console=console_log, save_log=save_log)

        # ── 启动浏览器 ──
        self._browser = BrowserManager(browser_path, user_data_dir)
        self._browser.start()

        # ── 先尝试已有 Cookie ──
        if self._browser.verify_cookies():
            self._emit("progress", "登录状态有效，无需重新登录")
        else:
            self._emit("progress", "登录状态无效，请在浏览器中登录 Boss 直聘")
            if not self.login():
                raise RuntimeError("Boss直聘登录超时，请重新运行")

        self._my_user_id: int | None = None

    # ═══════════════════════════════════════════════════════════════════
    #  公开方法 — login / refresh_session
    # ═══════════════════════════════════════════════════════════════════

    def login(self) -> bool:
        """跳转到登录页面，等待用户手动登录。

        成功返回 True，超时返回 False。
        """
        self._emit("progress", "正在跳转到登录页面...")
        self._browser.tab.get("https://www.zhipin.com/web/user/")
        ok = self._browser.wait_for_login()
        if ok:
            self._emit("progress", "登录成功")
        else:
            self._emit("error", "登录超时，请重新运行")
        return ok

    def refresh_session(self) -> bool:
        """刷新 session 并验证 Cookie。

        1. 导航到 geek/job 刷新页面上下文
        2. 验证 Cookie
        3. 无效则自动调用 login()
        """
        self._emit("progress", "正在刷新 session...")
        self._browser.refresh_page()
        if self._browser.verify_cookies():
            self._emit("progress", "Session 刷新成功")
            return True
        self._emit("progress", "刷新后 Cookie 无效，需要重新登录")
        return self.login()


__all__ = [
    "BossZhipin",
    "JobSummary", "JobDetail",
    "CITY_CODES", "SALARY_CODES", "EXP_CODES", "DEGREE_CODES",
    "INDUSTRY_CODES", "SCALE_CODES", "STAGE_CODES", "JOB_TYPE_CODES",
]
__version__ = "2.0.0"
