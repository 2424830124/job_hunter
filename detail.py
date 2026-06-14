"""
Boss直聘岗位抓取系统 - 批量详情查看模块
优先 httpx + cookie 直接调 API，降级 Scrapling 页面解析。
"""

import logging
import random
import time

import httpx

try:
    from scrapling import Selector
    _has_scrapling = True
except ImportError:
    _has_scrapling = False

from ._core.browser import BrowserManager
from ._core.human import HumanSimulator
from ._core.config import DetailConfig, BOSS_CONFIG
from ._core.constants import DETAIL_API
from ._core.parsers import JobSummary, JobDetail, extract_job_detail_from_api

logger = logging.getLogger(__name__)


# ── Scrapling 辅助函数 ──────────────────────────────────────────────
def _first(el) -> str:
    try:
        t = el.text if hasattr(el, 'text') else str(el)
        return t.strip().split("\n")[0].strip()
    except Exception:
        return ""

def _css_first(page: Selector, selector: str) -> str:
    try:
        els = page.css(selector)
        if els:
            return _first(els[0])
    except Exception:
        pass
    return ""

def _css_text(page: Selector, selector: str) -> str:
    try:
        els = page.css(selector)
        if els:
            t = els[0].get_all_text() or els[0].text or ""
            return t.strip()
    except Exception:
        pass
    return ""

def _css_all_text(page: Selector, selector: str) -> list[str]:
    result = []
    try:
        for e in page.css(selector):
            t = (e.get_all_text() or e.text or "").strip()
            if t:
                result.append(t)
    except Exception:
        pass
    return result


class DetailFetcher:
    """批量详情查看模块。"""

    def __init__(self, browser: BrowserManager, human: HumanSimulator, config: DetailConfig | None = None):
        self._browser = browser
        self._human = human
        self._config = config or BOSS_CONFIG.detail

    def fetch_one(self, job_id: str, security_id: str = "") -> JobDetail | None:
        job = JobSummary(job_id=job_id, security_id=security_id)
        return self._fetch_one_impl(job)

    # --------------------------------------------------------
    # 核心：优先 API，降级 Scrapling
    # --------------------------------------------------------
    def _fetch_one_impl(self, job: JobSummary) -> JobDetail | None:
        if not job.job_id:
            logger.warning("缺少 encryptJobId")
            return None

        detail_url = self._config.detail_url_template.format(encrypt_id=job.job_id)

        for attempt in range(1, self._config.max_retries + 1):
            try:
                # 优先 httpx 直接调 API
                detail = self._fetch_via_api(job, detail_url)
                if detail and detail.job_description:
                    return detail

                # 降级 Scrapling
                detail = self._fetch_via_scrapling(job, detail_url)
                if detail and detail.job_description:
                    return detail

                logger.warning("第 %d 次未提取到详情", attempt)
            except Exception as e:
                logger.error("详情异常 (attempt %d): %s", attempt, e)
            if attempt < self._config.max_retries:
                time.sleep(random.uniform(3.0, 8.0))
        return None

    # --------------------------------------------------------
    # httpx 直接调 API
    # --------------------------------------------------------
    def _fetch_via_api(self, job: JobSummary, detail_url: str) -> JobDetail | None:
        """用浏览器 cookie 直接调详情 API。"""
        cookies, headers = self._browser.build_headers("https://www.zhipin.com/web/geek/job")

        for attempt in range(2):
            try:
                resp = httpx.get(DETAIL_API,
                    params={"securityId": job.security_id or job.job_id},
                    cookies=cookies, headers=headers, timeout=15)
                data = resp.json()

                if data.get("code") == 37:
                    cookies = self._browser.refresh_session()
                    headers["zp_token"] = cookies.get("bst", "")
                    continue

                detail = extract_job_detail_from_api(data, job.job_id, detail_url)
                if detail and detail.job_description:
                    logger.debug("[API] %s @ %s", detail.job_name, detail.company_name)
                    return detail
                if attempt == 0:
                    time.sleep(3)
            except Exception as e:
                if attempt == 0:
                    time.sleep(3)
                else:
                    logger.debug("API 请求失败: %s", e)
        return None

    # --------------------------------------------------------
    # Scrapling 页面解析（降级）
    # --------------------------------------------------------
    def _fetch_via_scrapling(self, job: JobSummary, detail_url: str) -> JobDetail | None:
        tab = self._browser.tab
        self._browser.ensure_stealth()

        tab.get(detail_url)
        time.sleep(random.uniform(2, 3))

        try:
            body = tab.ele("tag:body", timeout=2)
            if body and body.text:
                if "安全验证" in body.text[:500] or "验证码" in body.text[:500]:
                    logger.warning("验证码拦截")
                    return None
        except Exception:
            pass

        html = tab.html
        if not html:
            return None

        try:
            if not _has_scrapling:
                return None
            page = Selector(html)
        except Exception:
            return None

        job_name = (
            _css_first(page, "h1") or _css_first(page, ".name")
            or _css_first(page, ".job-name") or _css_first(page, "[class*='job-name']")
        )
        salary = _css_first(page, ".salary") or _css_first(page, "[class*='salary']")
        jd_text = ""
        for sel in [".job-sec-text", ".job-detail", ".detail-content",
                     "[class*='job-detail']", "[class*='description']",
                     "[class*='job-sec']", ".job-desc", "[class*='desc']"]:
            t = _css_text(page, sel)
            if t and len(t) > 30:
                jd_text = t
                break
        if not jd_text:
            for sel in ["main", "[class*='content']", "[class*='detail']", "article"]:
                t = _css_text(page, sel)
                if t and len(t) > 50:
                    jd_text = t
                    break

        company_name = (
            _css_first(page, ".company-name a") or _css_first(page, ".company-name")
            or _css_first(page, "[class*='company-name']")
        )
        skills = _css_all_text(page, ".tag-list span") or _css_all_text(page, "[class*='tag'] span")
        skills = list(dict.fromkeys(skills))

        experience = education = city = ""
        for v in _css_all_text(page, ".tag-list li") + _css_all_text(page, "[class*='info'] span"):
            if not experience and any(k in v for k in ["年", "经验", "在校", "应届", "不限"]):
                experience = v
            elif not education and any(k in v for k in ["本科", "大专", "硕士", "博士", "学历"]):
                education = v
            elif not city and ("市" in v or "区" in v):
                city = v

        company_size = company_stage = company_industry = ""
        for v in _css_all_text(page, ".company-tag-list li") + _css_all_text(page, "[class*='company-tag']"):
            if "人" in v:
                company_size = v
            elif any(k in v for k in ["轮", "上市", "融资"]):
                company_stage = v
            elif len(v) > 2 and not company_industry:
                company_industry = v

        boss_name = _css_first(page, ".boss-name") or _css_first(page, "[class*='boss'] .name") or ""

        if not job_name and not jd_text:
            return None

        return JobDetail(
            job_id=job.job_id, security_id=job.security_id,
            job_name=job_name, salary=salary, city=city,
            experience=experience, education=education,
            skills=skills, job_description=jd_text,
            company_name=company_name, company_size=company_size,
            company_stage=company_stage, company_industry=company_industry,
            boss_name=boss_name, job_url=detail_url,
            fetched_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        )
