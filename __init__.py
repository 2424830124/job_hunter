"""job_hunter — Boss直聘岗位抓取 SDK

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

import copy
import json
import logging
import time
from pathlib import Path

import httpx

from ._core.config import BOSS_CONFIG, BossConfig, CITY_CODES
from ._core.browser import BrowserManager
from ._core.human import HumanSimulator
from ._core.parsers import JobSummary, JobDetail, job_summary_to_api_dict, job_detail_to_api_dict
from ._core.logger import setup_logger
from ._core.constants import GREET_API
from .search import JobSearcher
from .detail import DetailFetcher

logger = logging.getLogger(__name__)

__version__ = "1.0.0"
__all__ = [
    "BossZhipin",
    "BossConfig",
    "BOSS_CONFIG",
    "CITY_CODES",
    "JobSummary",
    "JobDetail",
]


def _make_key(job_name: str, job_id: str, seen: dict) -> str:
    """生成不重名的 dict 键；重名时附加 id 后6位。"""
    if job_name not in seen:
        seen[job_name] = job_id
        return job_name
    return f"{job_name}_{job_id[-6:]}"


class BossZhipin:
    """Boss直聘 SDK，__init__ 自动完成浏览器启动与登录。"""

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
        """
        Args:
            browser_path: Edge 浏览器可执行文件路径（必填）
            user_data_dir: 浏览器用户数据目录（必填）
            output_dir:    结果保存目录（必填）
            log_dir:       日志目录（必填）
            save_results:  是否自动保存为 JSON 文件
            save_log:      是否写入日志文件
            console_log:   是否输出日志到控制台
            on_message:    可选 GUI 回调 (msg: dict) -> None
                           msg = {"type": "progress"|"error", "message": "..."}
        """
        self._on_message = on_message

        for name, val in [("browser_path", browser_path), ("user_data_dir", user_data_dir),
                          ("output_dir", output_dir), ("log_dir", log_dir)]:
            if not val:
                raise ValueError(f"{name} 为必填参数，不能为空")

        self._save_results = save_results
        self._config: BossConfig = copy.deepcopy(BOSS_CONFIG)
        self._config.browser.browser_path = browser_path
        self._config.browser.user_data_dir = user_data_dir
        self._config.output.output_dir = output_dir
        self._config.output.log_dir = log_dir

        setup_logger(log_dir=self._config.output.log_dir, console=console_log, save_log=save_log)

        self._browser = BrowserManager(self._config.browser)
        self._browser.start()
        if not self._browser.wait_for_login():
            raise RuntimeError("Boss直聘登录超时，请重新运行")

        tab = self._browser.tab
        self._human = HumanSimulator(tab, self._config.human)
        self._searcher = JobSearcher(self._browser, self._config.search)
        self._detail = DetailFetcher(self._browser, self._human, self._config.detail)

    def _emit(self, type: str, message: str) -> None:
        """发送消息到回调（GUI）和日志。"""
        logger.info(message)
        if self._on_message:
            try:
                self._on_message({"type": type, "message": message})
            except Exception:
                pass

    # ── 公开方法 ──────────────────────────────────────────────

    def search(self, keyword: str, city: str = "101010100", count: int = 15) -> dict:
        """关键词搜索岗位。

        Args:
            keyword: 搜索关键词
            city:    城市编码或中文名（如 "杭州"、"101010100"），默认全国
            count:   最多返回条数

        Returns:
            dict，以岗位名称为键::

                {
                    "Python工程师": {
                        "security_id":      "snASzZoB...",   # 安全ID，调详情API用
                        "encrypt_id":       "13228...",       # 加密岗位ID
                        "degree":           "大专",           # 学历要求
                        "experience":       "经验不限",        # 经验要求
                        "skills":           ["Python","Go"],  # 技能标签
                        "salary":           "9-10K",          # 薪资
                        "city":             "杭州",            # 城市
                        "company":          "某科技公司",      # 公司名
                        "size":             "0-20人",         # 公司规模
                        "financing":        "不需要融资",      # 融资阶段
                        "industry":         "人工智能",        # 行业
                        "dialogue":         false,            # 是否沟通过
                        "boss_name":        "张经理",          # 招聘者名称
                        "boss_id":          "673235...",      # 招聘者ID
                        "area_district":    "余杭区",          # 行政区
                        "business_district":"仓前",           # 商圈
                        "job_labels":       ["应届","大专"],   # 岗位标签
                        "welfare_list":     ["五险一金","双休"],# 福利
                    }
                }
        """
        self._searcher._config.keywords = [keyword]
        self._searcher._config.city_code = self._config.search._resolve_city(city)
        self._searcher._collected = {}
        jobs = self._searcher.run(max_jobs=count)
        result = self._jobs_to_dict(jobs[:count])
        self._emit("progress", f"搜索完成: {keyword} → {len(result)} 个岗位")
        if self._save_results:
            self._save(result, prefix="search")
        return result

    def fetch_detail(self, security_id: str, encrypt_job_id: str = "") -> dict:
        """抓取单个岗位的完整详情。

        Args:
            security_id:    安全ID（从搜索结果中获取）
            encrypt_job_id: 加密岗位ID（可选，降级方案需要）

        Returns:
            dict::

                {
                    "job":              "Python工程师",     # 岗位名称
                    "security_id":      "snASzZoB...",      # 安全ID
                    "encrypt_id":       "13228...",          # 加密岗位ID
                    "detail":           "岗位职责:...",      # 完整JD文本
                    "degree":           "本科",              # 学历要求
                    "experience":       "3-5年",            # 经验要求
                    "skills":           ["Python","Django"],# 技能标签
                    "salary":           "20K-40K",          # 薪资
                    "city":             "杭州",             # 城市
                    "company":          "某科技有限公司",     # 公司名
                    "size":             "500-999人",        # 公司规模
                    "financing":        "B轮",              # 融资阶段
                    "industry":         "互联网",           # 行业
                    "dialogue":         false,              # 是否沟通过
                    "boss_name":        "张经理",           # 招聘者名称
                    "boss_id":          "abc123...",        # 招聘者ID
                    "address":          "杭州余杭区",        # 工作地址
                    "recruitment_count":"2人",              # 招聘人数
                    "position_name":    "Python",           # 职位类别
                    "job_status":       "招聘中",           # 岗位状态
                    "pay_type":         "月薪",             # 薪资类型
                }

            失败时返回 {"error": "...", "id": security_id}。
        """
        try:
            detail = self._detail.fetch_one(encrypt_job_id, security_id=security_id)
            if detail is None:
                return {"error": "抓取失败", "id": security_id}
            return job_detail_to_api_dict(detail)
        except Exception as exc:
            logger.error("fetch_detail 异常: %s", exc)
            return {"error": str(exc), "id": security_id}

    def contact(self, security_id: str, lid: str = "") -> str:
        """打招呼。返回 \"succeed\" 或失败原因。"""
        cookies, headers = self._browser.build_headers("https://www.zhipin.com/web/geek/job")
        params = {"securityId": security_id}
        if lid: params["lid"] = lid

        for attempt in range(2):  # 最多2次（首次+1次重试）
            try:
                resp = httpx.get(GREET_API, params=params, cookies=cookies, headers=headers, timeout=15)
                data = resp.json()

                if data.get("code") == 37:
                    cookies = self._browser.refresh_session()
                    headers["zp_token"] = cookies.get("bst", "")
                    resp = httpx.get(GREET_API, params=params, cookies=cookies, headers=headers, timeout=15)
                    data = resp.json()

                code = data.get("code")
                if code == 0:
                    self._emit("progress", "打招呼成功")
                    return "succeed"

                msg = data.get("message", f"code={code}")
                if attempt == 0:
                    time.sleep(3)
                    continue  # 重试
                self._emit("error", f"打招呼失败: {msg}")
                return msg
            except Exception as exc:
                if attempt == 0:
                    time.sleep(3)
                    continue
                self._emit("error", f"打招呼异常: {exc}")
                return str(exc)
        return "未知错误"

    def get_chat_list(self) -> list[dict]:
        """获取全部会话列表。

        Returns:
            list[dict]，每条::

                {
                    "uid":         526279477,       # 会话唯一ID
                    "name":        "刘建军",         # 招聘者名称
                    "company":     "杭州学慧苑",     # 公司名
                    "title":       "HR",            # 招聘者职位
                    "last_msg":    "在杭州吗",       # 最后一条消息
                    "last_time":   "昨天",           # 最后消息时间
                    "last_sender": "boss",          # 最后发言人 "me"/"boss"
                    "unread":      true,            # 是否有未读（boss最后发言）
                }
        """
        raw = self._get_raw_chats()
        my_id = self._my_user_id()
        result = []
        for c in raw:
            info = c.get("lastMessageInfo", {}) or {}
            if isinstance(info, str):
                try: info = json.loads(info)
                except: info = {}
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
        return result

    def close(self) -> None:
        """断开浏览器连接（保留浏览器进程和登录态）。"""
        self._browser.close()

    # ── 内部方法 ──────────────────────────────────────────────

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

    def _my_user_id(self) -> int:
        cookies, headers = self._browser.build_headers("https://www.zhipin.com/web/geek/chat")
        try:
            resp = httpx.get("https://www.zhipin.com/wapi/zpuser/wap/getUserInfo.json",
                            cookies=cookies, headers=headers, timeout=10)
            return resp.json().get("zpData", {}).get("userId", 0)
        except Exception:
            return 0

    def _jobs_to_dict(self, jobs: list[JobSummary]) -> dict:
        result: dict = {}
        seen: dict = {}
        for job in jobs:
            key = _make_key(job.job_name, job.job_id, seen)
            result[key] = job_summary_to_api_dict(job)
        return result

    def _save(self, data: dict, prefix: str) -> None:
        try:
            output_dir = Path(self._config.output.output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            ts = time.strftime("%Y%m%d_%H%M%S")
            path = output_dir / f"{prefix}_{ts}.json"
            path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("结果已保存: %s (%d条)", path, len(data))
        except Exception as exc:
            logger.warning("保存失败: %s", exc)
