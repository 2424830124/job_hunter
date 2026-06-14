# -*- coding: utf-8 -*-
"""
Boss直聘岗位抓取系统 - 全局配置模块

使用 dataclass 管理所有配置项。各子配置通过 :class:`BossConfig` 聚合，
全局单例为 :data:`BOSS_CONFIG`。

城市中文名与编码的映射见 :data:`CITY_CODES`。
"""

from dataclasses import dataclass, field
from pathlib import Path

# ============================================================
# 项目根目录（指向 job_hunter/ 包目录，而非 _core/）
# ============================================================
PROJECT_ROOT: Path = Path(__file__).parent.parent


# ============================================================
# 城市编码字典（中文名 → 数字编码）
# ============================================================
CITY_CODES: dict[str, str] = {
    "全国": "100010000",
    # 一线
    "北京": "101010100",
    "上海": "101020100",
    "广州": "101280100",
    "深圳": "101280600",
    # 新一线
    "杭州": "101210100",
    "成都": "101270100",
    "南京": "101190100",
    "武汉": "101200100",
    "西安": "101110100",
    "苏州": "101190400",
    "长沙": "101250100",
    "天津": "101030100",
    "重庆": "101040100",
    "郑州": "101180100",
    "东莞": "101281600",
    "佛山": "101280800",
    "合肥": "101220100",
    "青岛": "101120200",
    "宁波": "101210400",
    "沈阳": "101070100",
    "昆明": "101290100",
    # 二线
    "大连": "101070200",
    "厦门": "101230200",
    "珠海": "101280700",
    "无锡": "101190200",
    "福州": "101230100",
    "济南": "101120100",
    "哈尔滨": "101050100",
    "长春": "101060100",
    "南昌": "101240100",
    "贵阳": "101260100",
    "南宁": "101300100",
    "石家庄": "101090100",
    "太原": "101100100",
    "兰州": "101160100",
    "海口": "101310100",
    "常州": "101191100",
    "温州": "101210700",
    "嘉兴": "101210300",
    "徐州": "101190800",
    # 特别行政区
    "香港": "101320100",
}


# ============================================================
# 筛选编码字典（中文名 → API 编码）
# ============================================================
SALARY_CODES: dict[str, str] = {
    "3K以下": "401",
    "3-5K": "402",
    "5-10K": "403",
    "10-15K": "404",
    "15-20K": "405",
    "20-30K": "406",
    "30-50K": "407",
    "50K以上": "408",
}

EXP_CODES: dict[str, str] = {
    "不限": "0",
    "在校/应届": "108",
    "应届生": "108",
    "1年以内": "101",
    "1-3年": "102",
    "3-5年": "103",
    "5-10年": "104",
    "10年以上": "105",
}

DEGREE_CODES: dict[str, str] = {
    "不限": "0",
    "初中及以下": "209",
    "中专/中技": "208",
    "高中": "206",
    "大专": "202",
    "本科": "203",
    "硕士": "204",
    "博士": "205",
}

INDUSTRY_CODES: dict[str, str] = {
    "不限": "0",
    "互联网": "100020",
    "电子商务": "100021",
    "游戏": "100024",
    "软件/信息服务": "100032",
    "人工智能": "100901",
    "大数据": "100902",
    "云计算": "100903",
    "区块链": "100904",
    "物联网": "100905",
    "金融": "100101",
    "银行": "100102",
    "保险": "100103",
    "证券/基金": "100104",
    "教育培训": "100200",
    "医疗健康": "100300",
    "房地产": "100400",
    "汽车": "100500",
    "物流/运输": "100600",
    "广告/传媒": "100700",
    "消费品": "100800",
    "制造业": "101000",
    "能源/环保": "101100",
    "政府/非营利": "101200",
    "农业": "101300",
}

SCALE_CODES: dict[str, str] = {
    "不限": "0",
    "0-20人": "301",
    "20-99人": "302",
    "100-499人": "303",
    "500-999人": "304",
    "1000-9999人": "305",
    "10000人以上": "306",
}

STAGE_CODES: dict[str, str] = {
    "不限": "0",
    "未融资": "801",
    "天使轮": "802",
    "A轮": "803",
    "B轮": "804",
    "C轮": "805",
    "D轮及以上": "806",
    "已上市": "807",
    "不需要融资": "808",
}

JOB_TYPE_CODES: dict[str, str] = {
    "全职": "1901",
    "实习": "1902",
    "兼职": "1903",
}


@dataclass
class BrowserConfig:
    """
    浏览器接管配置。

    控制 DrissionPage 如何启动/接管真实 Edge 浏览器。
    所有路径字段均为字符串，由 :class:`~job_hunter.BossZhipin` 构造函数注入。
    """

    # Edge 浏览器可执行文件路径
    browser_path: str = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    # CDP 远程调试端口
    remote_debugging_port: int = 9222
    # 用户数据目录（保存在项目路径下，保持登录态）；必填，由 BossZhipin 构造函数传入
    user_data_dir: str = ""
    # 是否使用无头模式（Boss直聘必须可视化操作，禁用无头）
    headless: bool = False
    # 浏览器启动后等待用户手动登录的最大时间（秒）
    login_wait_timeout: int = 300
    # 登录检测 Cookie 名称
    login_cookie_name: str = "__zp_stoken__"
    # 基础启动参数
    arguments: list[str] = field(default_factory=lambda: [
        "--disable-blink-features=AutomationControlled",   # 禁用自动化标记
        "--disable-infobars",                              # 隐藏信息栏
        "--no-first-run",                                  # 跳过首次运行向导
        "--disable-extensions",                            # 禁用扩展（减少指纹）
        "--disable-popup-blocking",                        # 允许弹窗
        "--disable-default-apps",                          # 禁用默认应用
        "--disable-gpu",                                   # 禁用 GPU 加速（稳定性）
        "--window-size=1920,1080",                         # 固定窗口尺寸
    ])


@dataclass
class SearchConfig:
    """
    搜索配置（纯 API 模式）。

    ``page_start`` / ``page_end`` 仍保留字段以兼容外部代码；
    实际翻页逻辑由 :class:`~job_hunter.search.JobSearcher` 的 ``max_jobs`` 参数控制。
    """

    keywords: list[str] = field(default_factory=lambda: ["Python", "数据分析"])
    city_code: str = "101010100"  # 城市编码，支持中文名
    page_start: int = 1   # unused, kept for compatibility
    page_end: int = 3     # unused, kept for compatibility
    # 筛选参数
    salary: str | None = None
    experience: str | None = None
    degree: str | None = None
    industry: str | None = None
    scale: str | None = None
    stage: str | None = None
    job_type: str | None = None

    def _resolve_city(self, city: str) -> str:
        """
        将城市名或编码统一解析为数字编码。

        - 中文名（如 ``"北京"``）→ 查 :data:`CITY_CODES` 返回对应编码
        - 已是纯数字编码（如 ``"101010100"``）→ 直接返回
        - 未识别 → 返回原值（调用方自行处理）

        Args:
            city: 城市中文名或数字编码字符串。

        Returns:
            数字编码字符串。
        """
        if city.isdigit():
            return city
        return CITY_CODES.get(city, city)


@dataclass
class DetailConfig:
    """详情页配置。"""

    detail_url_template: str = "https://www.zhipin.com/job_detail/{encrypt_id}.html"
    max_retries: int = 2



@dataclass
class HumanBehaviorConfig:
    """
    人类行为模拟配置（仅 Scrapling 降级时使用）。

    大部分字段当前未被主流程读取，保留以维持 API 兼容性。
    """

    mouse_move_steps_min: int = 10    # unused, kept for compatibility
    mouse_move_steps_max: int = 30    # unused, kept for compatibility
    mouse_offset_min: int = -5        # unused, kept for compatibility
    mouse_offset_max: int = 5         # unused, kept for compatibility
    action_delay_min: float = 0.5     # unused, kept for compatibility
    action_delay_max: float = 2.0     # unused, kept for compatibility
    scroll_distance_min: int = 200    # unused, kept for compatibility
    scroll_distance_max: int = 600    # unused, kept for compatibility
    scroll_pause_min: float = 1.0     # unused, kept for compatibility
    scroll_pause_max: float = 3.0     # unused, kept for compatibility
    token_bucket_capacity: int = 1    # unused, kept for compatibility
    token_refill_rate: float = 0.2    # unused, kept for compatibility


@dataclass
class OutputConfig:
    """输出配置。"""

    output_dir: str = ""    # 必填，由 BossZhipin 构造函数传入
    log_dir: str = ""       # 必填，由 BossZhipin 构造函数传入
    log_level: str = "INFO"
    output_format: str = "json"


@dataclass
class BossConfig:
    """Boss直聘抓取系统总配置，聚合所有子配置。"""

    browser: BrowserConfig = field(default_factory=BrowserConfig)
    search: SearchConfig = field(default_factory=SearchConfig)
    detail: DetailConfig = field(default_factory=DetailConfig)
    human: HumanBehaviorConfig = field(default_factory=HumanBehaviorConfig)
    output: OutputConfig = field(default_factory=OutputConfig)


# 全局单例配置
BOSS_CONFIG = BossConfig()
