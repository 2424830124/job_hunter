import logging
from .base import BaseMixin
from .browser import BrowserManager

__all__ = ["BaseMixin", "BrowserManager"]

_logger = logging.getLogger(__name__)

# ── BossZhipin ──────────────────────────────────────────────────

from ..jobs import SearchMixin, DetailMixin
from ..dialogue import ChatMixin, ContactMixin
from ..personal import ResumeMixin, InterviewMixin


class BossZhipin(
    SearchMixin, DetailMixin,
    ChatMixin, ContactMixin,
    InterviewMixin, ResumeMixin,
):
    """Boss直聘 SDK — 自动管理浏览器登录态，统一错误处理。"""

    def __init__(
        self,
        browser_path: str,
        user_data_dir: str,
        output_dir: str,
        log_dir: str,
        save_results: bool = True,
        console_log: bool = True,
        save_log: bool = True,
        on_message: callable = None,
    ):
        for name, val in [
            ("browser_path", browser_path), ("user_data_dir", user_data_dir),
            ("output_dir", output_dir), ("log_dir", log_dir),
        ]:
            if not val: raise ValueError(f"{name} 为必填参数")

        self._output_dir = output_dir
        self._save_results = save_results
        self._on_message = on_message

        from ..assets.logger import setup_logger
        setup_logger(log_dir=log_dir, console=console_log, save_log=save_log)

        self._browser = BrowserManager(browser_path, user_data_dir)
        self._browser.start()

        if self._browser.verify_cookies():
            _logger.info("登录状态有效")
        else:
            if not self.login():
                raise RuntimeError("登录超时")