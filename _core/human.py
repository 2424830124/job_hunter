# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 人类行为模拟模块

⚠️ 仅在 Scrapling 页面解析降级时使用。
API 模式下不需要任何行为模拟。

保留 ``HumanSimulator`` 类结构以保持 API 兼容性；
未在当前主流程中调用的方法已标注 ``# unused, kept for API compatibility``。
"""

import logging
import random
import time

from DrissionPage import ChromiumPage

from .config import HumanBehaviorConfig, BOSS_CONFIG

logger = logging.getLogger(__name__)


class TokenBucket:
    """令牌桶算法（当前 API 模式未使用，保留以供未来扩展）。"""

    def __init__(self, capacity: int = 1, refill_rate: float = 0.2):
        self._capacity = capacity
        self._refill_rate = refill_rate
        self._tokens = float(capacity)
        self._last_refill = time.monotonic()

    def acquire(self, timeout: float = 120.0) -> bool:
        deadline = time.monotonic() + timeout
        while True:
            now = time.monotonic()
            elapsed = now - self._last_refill
            self._tokens = min(self._capacity, self._tokens + elapsed * self._refill_rate)
            self._last_refill = now
            if self._tokens >= 1.0:
                self._tokens -= 1.0
                return True
            remaining = deadline - now
            if remaining <= 0:
                return False
            wait = min(0.5, remaining)
            time.sleep(wait)


class HumanSimulator:
    """
    人类行为模拟器。

    封装鼠标轨迹、随机延迟、滚动行为等方法。
    当前仅 :py:meth:`simulate_reading` 和 :py:meth:`idle_movement` 在
    Scrapling 降级路径中被调用；其余方法保留以维持 API 兼容性。

    Args:
        page:   DrissionPage ``ChromiumPage`` 实例（或当前标签页）。
        config: 人类行为配置，默认取 :data:`~.config.BOSS_CONFIG`.human。
    """

    def __init__(self, page: ChromiumPage, config: HumanBehaviorConfig | None = None):
        self._page = page
        self._config = config or BOSS_CONFIG.human
        logger.info("HumanSimulator 初始化完成")

    # --------------------------------------------------------
    # 随机延迟（unused, kept for API compatibility）
    # --------------------------------------------------------
    def random_delay(  # unused, kept for API compatibility
        self,
        min_sec: float | None = None,
        max_sec: float | None = None,
        label: str = "",
    ) -> None:
        """在指定区间内随机等待，模拟人类操作间的自然停顿。"""
        lo = min_sec if min_sec is not None else self._config.action_delay_min
        hi = max_sec if max_sec is not None else self._config.action_delay_max
        delay = random.uniform(lo, hi)
        logger.debug("随机延迟 %.2fs %s", delay, f"[{label}]" if label else "")
        time.sleep(delay)

    # --------------------------------------------------------
    # 鼠标移动（unused, kept for API compatibility）
    # --------------------------------------------------------
    def human_move_to(self, element: object, jitter: bool = True) -> None:  # unused, kept for API compatibility
        """模拟人类鼠标移动到目标元素。"""
        try:
            actions = self._page.actions
            actions.move_to(element)
            if jitter:
                offset_x = random.randint(self._config.mouse_offset_min, self._config.mouse_offset_max)
                offset_y = random.randint(self._config.mouse_offset_min, self._config.mouse_offset_max)
                actions.move(offset_x, offset_y)
            logger.debug("鼠标已移动到元素 (jitter=%s)", jitter)
        except Exception as e:
            logger.warning("鼠标移动失败: %s", e)

    # --------------------------------------------------------
    # 模拟点击（unused, kept for API compatibility）
    # --------------------------------------------------------
    def human_click(self, element: object, pre_delay: bool = True) -> None:  # unused, kept for API compatibility
        """模拟人类点击：先移动鼠标到元素位置，短暂停顿后点击。"""
        try:
            if pre_delay:
                self.random_delay(0.2, 0.6, "点击前停顿")
            self.human_move_to(element)
            self.random_delay(0.1, 0.3, "点击前微停顿")
            element.click()
            logger.debug("人类点击完成")
        except Exception as e:
            logger.warning("人类点击失败: %s", e)
            raise

    # --------------------------------------------------------
    # 模拟滚动（unused, kept for API compatibility）
    # --------------------------------------------------------
    def human_scroll(self, pixel: int | None = None, pause: bool = True) -> None:  # unused, kept for API compatibility
        """模拟人类滚动页面，每次滚动随机像素数，可选停顿。"""
        distance = pixel or random.randint(
            self._config.scroll_distance_min,
            self._config.scroll_distance_max,
        )
        try:
            self._page.scroll.down(distance)
            logger.debug("滚动 %d 像素", distance)
            if pause:
                pause_time = random.uniform(
                    self._config.scroll_pause_min,
                    self._config.scroll_pause_max,
                )
                time.sleep(pause_time)
        except Exception as e:
            logger.warning("滚动失败: %s", e)

    # --------------------------------------------------------
    # 模拟阅读停留（Scrapling 降级使用）
    # --------------------------------------------------------
    def simulate_reading(self, min_sec: float | None = None, max_sec: float | None = None) -> None:
        """
        模拟人类阅读页面内容的停留时间。

        在 Scrapling 降级路径访问详情页时调用，降低访问频率。

        Args:
            min_sec: 最短停留秒数，默认取 :attr:`DetailConfig.read_time_min`。
            max_sec: 最长停留秒数，默认取 :attr:`DetailConfig.read_time_max`。
        """
        lo = min_sec if min_sec is not None else BOSS_CONFIG.detail.read_time_min
        hi = max_sec if max_sec is not None else BOSS_CONFIG.detail.read_time_max
        read_time = random.uniform(lo, hi)
        logger.info("模拟阅读停留 %.1f 秒", read_time)
        time.sleep(read_time)

    # --------------------------------------------------------
    # 模拟人类滑动浏览（unused, kept for API compatibility）
    # --------------------------------------------------------
    def simulate_browse_scroll(self, rounds: int | None = None) -> int:  # unused, kept for API compatibility
        """
        模拟人类浏览列表页面：随机滚动 + 偶尔停顿 + 偶尔回滚。

        Returns:
            实际滚动次数。
        """
        max_rounds = rounds or random.randint(3, 8)
        for _ in range(max_rounds):
            self.human_scroll()
            if random.random() < 0.2:
                back_distance = random.randint(50, 150)
                try:
                    self._page.scroll.up(back_distance)
                    logger.debug("回滚 %d 像素", back_distance)
                    self.random_delay(0.5, 1.5, "回看停顿")
                except Exception:
                    pass
            if random.random() < 0.15:
                self.random_delay(2.0, 5.0, "阅读停顿")
        return max_rounds

    # --------------------------------------------------------
    # 模拟页面闲置（Scrapling 降级使用）
    # --------------------------------------------------------
    def idle_movement(self) -> None:
        """
        偶尔移动鼠标到随机位置，模拟用户无目的的鼠标移动。

        在 Scrapling 降级路径中使用，增加行为多样性。
        """
        try:
            actions = self._page.actions
            x = random.randint(100, 1820)
            y = random.randint(100, 980)
            actions.move_to((x, y))
            logger.debug("闲置移动鼠标到 (%d, %d)", x, y)
        except Exception as e:
            logger.debug("闲置鼠标移动失败: %s", e)
