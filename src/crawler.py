from __future__ import annotations

import argparse
import json
import logging
import random
import re
import time
from dataclasses import asdict, dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

LOGGER = logging.getLogger("guba-crawler")

DATE_XPATH = "//ul[@id='list']/li/div[2]/div[1]/div[2]"
CONTENT_XPATH = "//ul[@id='list']/li/div[2]/a/div[2]"
LIST_XPATH = "//ul[@id='list']/li"


@dataclass(frozen=True)
class Post:
    date: str
    text: str
    source_url: str


def parse_post_date(raw_value: str, start_date: date, end_date: date) -> date | None:
    raw_value = raw_value.strip()
    full_match = re.search(
        r"(?P<year>20\d{2})[-/.](?P<month>\d{1,2})[-/.](?P<day>\d{1,2})",
        raw_value,
    )
    if full_match:
        try:
            return date(
                int(full_match.group("year")),
                int(full_match.group("month")),
                int(full_match.group("day")),
            )
        except ValueError:
            return None

    short_match = re.search(r"(?P<month>\d{1,2})[-/.](?P<day>\d{1,2})", raw_value)
    if not short_match:
        return None

    month = int(short_match.group("month"))
    day = int(short_match.group("day"))
    candidates: list[date] = []
    for year in range(start_date.year - 1, end_date.year + 2):
        try:
            candidates.append(date(year, month, day))
        except ValueError:
            continue

    if not candidates:
        return None

    inside_window = [item for item in candidates if start_date <= item <= end_date]
    if inside_window:
        return inside_window[0]

    midpoint = start_date + (end_date - start_date) / 2
    return min(candidates, key=lambda item: abs(item - midpoint))


def clean_post_text(text: str) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) < 2:
        return ""
    if text.lower().startswith(("http://", "https://")):
        return ""
    if re.fullmatch(r"[\W_]+", text, flags=re.UNICODE):
        return ""
    if re.fullmatch(r"\d+", text):
        return ""
    return text


def click_if_present(driver: webdriver.Chrome, xpath: str, timeout: float = 1.5) -> None:
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((By.XPATH, xpath))
        )
        element.click()
    except (TimeoutException, WebDriverException):
        return


def dismiss_optional_popups(driver: webdriver.Chrome) -> None:
    click_if_present(driver, "//img[contains(@onclick, 'tk_tg_zoomin()')]")
    click_if_present(driver, "//*[@data-tracker-eventcode='gb.ggb.qhzy']")
    click_if_present(driver, "//*[@data-tracker-eventcode='gb.ggb.zxft']")


def build_driver(headless: bool) -> webdriver.Chrome:
    options = Options()
    options.page_load_strategy = "normal"
    options.add_argument("--lang=zh-CN")
    options.add_argument("--disable-blink-features=AutomationControlled")
    if headless:
        options.add_argument("--headless=new")
    return webdriver.Chrome(options=options)


def crawl_page(
    driver: webdriver.Chrome,
    url: str,
    start_date: date,
    end_date: date,
    delay_seconds: float,
) -> list[Post]:
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.XPATH, LIST_XPATH))
    )
    dismiss_optional_popups(driver)

    date_nodes = driver.find_elements(By.XPATH, DATE_XPATH)
    content_nodes = driver.find_elements(By.XPATH, CONTENT_XPATH)
    posts: list[Post] = []

    for date_node, content_node in zip(date_nodes, content_nodes):
        post_date = parse_post_date(date_node.text, start_date, end_date)
        if post_date is None or not start_date <= post_date <= end_date:
            continue

        text = clean_post_text(content_node.text)
        if not text:
            continue

        posts.append(
            Post(
                date=post_date.isoformat(),
                text=text,
                source_url=url,
            )
        )

    time.sleep(delay_seconds + random.uniform(0.0, 0.25))
    return posts


def crawl(
    symbol: str,
    start_page: int,
    end_page: int,
    start_date: date,
    end_date: date,
    output: Path,
    headless: bool,
    delay_seconds: float,
    append: bool,
) -> int:
    if start_page > end_page:
        raise ValueError("start_page must be less than or equal to end_page")
    if start_date > end_date:
        raise ValueError("start_date must be before end_date")

    mode = "a" if append else "w"
    output.parent.mkdir(parents=True, exist_ok=True)
    driver = build_driver(headless=headless)
    total = 0

    try:
        with output.open(mode, encoding="utf-8") as output_file:
            for page in range(start_page, end_page + 1):
                url = f"https://guba.eastmoney.com/list,{symbol}_{page}.html"
                LOGGER.info("Crawling page %s: %s", page, url)
                posts = crawl_page(
                    driver=driver,
                    url=url,
                    start_date=start_date,
                    end_date=end_date,
                    delay_seconds=delay_seconds,
                )
                for post in posts:
                    output_file.write(
                        json.dumps(asdict(post), ensure_ascii=False) + "\n"
                    )
                output_file.flush()
                total += len(posts)
    finally:
        driver.quit()

    return total


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Crawl Eastmoney Stock Bar posts.")
    parser.add_argument("--symbol", default="zssh000001")
    parser.add_argument("--start-page", type=int, required=True)
    parser.add_argument("--end-page", type=int, required=True)
    parser.add_argument("--start-date", type=date.fromisoformat, required=True)
    parser.add_argument("--end-date", type=date.fromisoformat, required=True)
    parser.add_argument("--output", type=Path, default=Path("data/posts.jsonl"))
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--delay", type=float, default=0.5)
    parser.add_argument("--append", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    args = build_parser().parse_args(argv)
    total = crawl(
        symbol=args.symbol,
        start_page=args.start_page,
        end_page=args.end_page,
        start_date=args.start_date,
        end_date=args.end_date,
        output=args.output,
        headless=args.headless,
        delay_seconds=args.delay,
        append=args.append,
    )
    LOGGER.info("Saved %s posts to %s", total, args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
