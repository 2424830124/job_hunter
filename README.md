# job_hunter

Boss 直聘岗位抓取 SDK。用你本机真实浏览器的登录态拿 Cookie，之后所有数据都走 httpx 直接调接口，不驱动页面渲染，比 Selenium 那一套快很多。

## 起因

找工作的时候每天手动刷岗位太费时间，就想把「搜岗位 → 看 JD → 打招呼」这条链路自动化掉。写的过程中发现难点根本不在解析页面，而在登录态和风控，所以改成了现在这个结构：浏览器只负责登一次，数据全部走 API。

## 能做什么

| 功能 | 说明 |
|---|---|
| 搜索岗位 | 关键词 + 城市，支持薪资 / 经验 / 学历 / 行业 / 规模 / 融资阶段筛选，返回结构化字段 |
| 岗位详情 | 完整 JD、技能标签、地址、招聘人数、岗位状态等 |
| 打招呼 | 一键开聊，返回 `succeed` 或失败原因（如「开聊提醒」） |
| 会话列表 | 拉取全部会话，带最后一条消息、发送方、是否未回复 |
| 面试邀请 | 面试邀请列表 |
| 我的简历 | 拉取自己的简历信息 |

## 环境要求

- Python >= 3.11
- 本机装了 Edge（用来提供登录态，程序会接管它）
- 目前只在 Windows 上测过

## 安装

```bash
git clone https://github.com/2424830124/job_hunter.git
cd job_hunter
pip install -r requirements.txt
```

只要最小依赖（不装详情页 DOM 降级用的 scrapling）：

```bash
pip install -e ".[minimal]"
```

## 快速开始

```python
from job_hunter import BossZhipin

a = BossZhipin(
    browser_path=r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    user_data_dir=r"./browser_data",   # 浏览器用户数据目录
    output_dir=r"./output",           # 结果保存目录
    log_dir=r"./logs",                # 日志目录
)

# 1. 搜索岗位（支持筛选）
jobs = a.search(keyword="Python", city="杭州")
jobs = a.search(keyword="Python", city="杭州", salary="20-30K", degree="本科", experience="3-5年")

# 2. 查看详情
detail = a.fetch_detail(security_id=jobs[0]["security_id"], encrypt_job_id=jobs[0]["encrypt_id"])

# 3. 打招呼
result = a.contact(security_id=jobs[0]["security_id"])

# 4. 会话列表 / 面试邀请 / 简历
chats = a.get_chat_list()
interviews = a.get_interviews()
resume = a.get_resume()

a.close()
```

**第一次运行会自己弹出一个 Edge 窗口**，在窗口里正常登录 Boss 直聘，程序检测到登录成功后会自动往下走；登录态存在 `user_data_dir` 里，以后不用再登。

## 技术上的几个取舍

**为什么不用 Selenium 全程驱动页面。**
页面上大量数据是异步渲染的，等元素、翻页、被反爬检测都会拖慢速度。这个项目只让浏览器干一件事：提供登录态 Cookie。拿到之后全部请求走 httpx 直接调接口，一次搜索请求不到一秒。

**Cookie 会过期，所以做了自愈。**
接口返回 `code=37` 表示 session 失效，代码检测到就自动刷新；如果登录彻底失效，会识别响应里的失登录关键词并触发重新登录流程，不用重启程序。

**为什么用 Mixin 拆。**
搜索/详情、聊天/打招呼、简历这三块的请求头和数据解析差别很大，塞在一个类里不好维护。按功能拆成独立模块后，加新功能只需要新增一个 Mixin。

## API

### 构造函数

```python
BossZhipin(
    browser_path: str,         # Edge 浏览器路径（必填）
    user_data_dir: str,        # 浏览器用户数据目录（必填）
    output_dir: str,           # 结果保存目录（必填）
    log_dir: str,              # 日志目录（必填）
    save_results: bool = True, # 是否自动保存 JSON
    console_log: bool = True,  # 是否输出到控制台
    save_log: bool = True,     # 是否写入日志文件
    on_message: callable = None,  # GUI 回调 (msg: dict) -> None
)
```

### `search(keyword, city="101010100", page=1, pagesize=15, salary=None, experience=None, degree=None, industry=None, scale=None, stage=None, job_type=None) -> list[dict] | None`

关键词搜索岗位。`city` 支持中文名（如「杭州」）或数字编码；筛选参数同样支持中文名（如 `salary="20-30K"`）或数字编码。失败返回 `None`。

返回字段：`security_id`, `encrypt_id`, `degree`, `experience`, `skills`, `salary`, `city`, `company`, `size`, `financing`, `industry`, `dialogue`, `boss_name`, `boss_id`, `area_district`, `business_district`, `job_labels`, `welfare_list`

### `fetch_detail(security_id, encrypt_job_id="") -> dict | None`

查看岗位完整详情。失败返回 `None`。

返回字段：`job`, `detail`（完整 JD）, `degree`, `experience`, `skills`, `salary`, `city`, `company`, `size`, `financing`, `industry`, `dialogue`, `boss_name`, `boss_id`, `address`, `recruitment_count`, `position_name`, `job_status`, `pay_type`

### `contact(security_id, lid="") -> str | None`

打招呼 / 开始沟通。返回 `"succeed"` 表示成功，否则返回失败原因（如 `"开聊提醒"`），网络异常返回 `None`。

### `get_chat_list() -> list[dict]`

获取全部会话列表。每条包含：`security_id`, `name`, `company`, `title`, `last_msg`, `last_time`, `last_sender`（`"me"` / `"boss"`）, `unreplied`

### `get_interviews() -> list[dict] | None`

获取面试邀请列表。失败返回 `None`。

### `get_resume() -> dict | None`

获取我的简历信息。返回 `{"baseinfo": {...}, "expect": {...}}`，失败返回 `None`。

### `close()`

断开浏览器连接。

## 项目结构

```
job_hunter/
├── __init__.py        BossZhipin（组合所有 Mixin）
├── _core/
│   ├── base.py        BaseMixin：_request / token / retry
│   └── browser.py     BrowserManager：Edge 接管 + Cookie
├── jobs.py            Search + Detail
├── dialogue.py        Chat + Contact + Interview
├── personal.py        Resume
└── assets/            常量 / 解析 / 工具
```

## 免责声明

本项目仅供学习和研究使用。使用本工具可能违反目标网站的用户协议，可能导致账号被限制或封禁。使用者需自行承担全部风险和责任，作者不承担任何因使用本工具导致的损失。

请合理控制请求频率，珍惜自己的账号。

## License

MIT
