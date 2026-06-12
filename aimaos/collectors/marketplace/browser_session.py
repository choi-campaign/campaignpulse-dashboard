from __future__ import annotations

from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import time


@dataclass(frozen=True)
class BrowserLaunchResult:
    status: str
    detail: str
    browser_executable: str = ""


@dataclass(frozen=True)
class ObservedPage:
    event: str
    url: str
    title: str
    page_index: int


@dataclass(frozen=True)
class AdCenterEntryCheckResult:
    status: str
    detail: str
    browser_executable: str
    started_url: str
    observed_pages: list[ObservedPage]
    popup_count: int


def playwright_installed() -> bool:
    return importlib.util.find_spec("playwright") is not None


def find_browser_executable() -> str:
    candidates = [
        os.getenv("AIMAOS_POC_BROWSER_EXECUTABLE", "").strip(),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            return candidate
    return ""


def smoke_launch_collection_browser(
    profile_dir: Path,
    download_dir: Path,
    *,
    headless: bool = False,
    target_url: str = "about:blank",
) -> BrowserLaunchResult:
    if not playwright_installed():
        return BrowserLaunchResult("failed", "Playwright package is not installed.")

    browser_executable = find_browser_executable()
    if not browser_executable:
        return BrowserLaunchResult("failed", "Chrome or Edge executable was not found.")

    try:
        from playwright.sync_api import sync_playwright

        profile_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                executable_path=browser_executable,
                headless=headless,
                accept_downloads=True,
                downloads_path=str(download_dir),
            )
            page = context.new_page()
            page.goto(target_url)
            context.close()
        return BrowserLaunchResult("success", "Dedicated collection browser launched.", browser_executable)
    except Exception as error:  # noqa: BLE001
        return BrowserLaunchResult("failed", str(error), browser_executable)


def open_manual_collection_browser(
    profile_dir: Path,
    download_dir: Path,
    *,
    target_url: str,
    wait_seconds: int = 300,
) -> BrowserLaunchResult:
    if not playwright_installed():
        return BrowserLaunchResult("failed", "Playwright package is not installed.")

    browser_executable = find_browser_executable()
    if not browser_executable:
        return BrowserLaunchResult("failed", "Chrome or Edge executable was not found.")

    try:
        from playwright.sync_api import sync_playwright

        profile_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                executable_path=browser_executable,
                headless=False,
                accept_downloads=True,
                downloads_path=str(download_dir),
            )
            page = context.new_page()
            page.goto(target_url or "about:blank")
            time.sleep(max(wait_seconds, 0))
            context.close()
        return BrowserLaunchResult(
            "success",
            f"Manual collection browser stayed open for {wait_seconds} seconds.",
            browser_executable,
        )
    except Exception as error:  # noqa: BLE001
        return BrowserLaunchResult("failed", str(error), browser_executable)


def watch_ad_center_entry(
    profile_dir: Path,
    download_dir: Path,
    *,
    target_url: str,
    wait_seconds: int = 300,
) -> AdCenterEntryCheckResult:
    if not playwright_installed():
        return AdCenterEntryCheckResult("failed", "Playwright package is not installed.", "", target_url, [], 0)

    browser_executable = find_browser_executable()
    if not browser_executable:
        return AdCenterEntryCheckResult("failed", "Chrome or Edge executable was not found.", "", target_url, [], 0)

    observed: list[ObservedPage] = []
    seen: set[tuple[str, str, int]] = set()
    popup_count = 0

    def record_page(event: str, page, page_index: int) -> None:
        url = ""
        title = ""
        try:
            url = page.url
        except Exception:  # noqa: BLE001
            url = ""
        try:
            title = page.title()
        except Exception:  # noqa: BLE001
            title = ""
        key = (event, url, page_index)
        if key not in seen:
            seen.add(key)
            observed.append(ObservedPage(event=event, url=url, title=title, page_index=page_index))

    def attach_page_handlers(page) -> None:
        page.on("popup", lambda popup: record_page("popup", popup, len(observed)))

    try:
        from playwright.sync_api import sync_playwright

        profile_dir.mkdir(parents=True, exist_ok=True)
        download_dir.mkdir(parents=True, exist_ok=True)
        with sync_playwright() as playwright:
            context = playwright.chromium.launch_persistent_context(
                user_data_dir=str(profile_dir),
                executable_path=browser_executable,
                headless=False,
                accept_downloads=False,
                downloads_path=str(download_dir),
            )

            def on_new_page(page) -> None:
                nonlocal popup_count
                popup_count += 1
                attach_page_handlers(page)
                record_page("new_page", page, len(context.pages) - 1)

            context.on("page", on_new_page)
            page = context.new_page()
            attach_page_handlers(page)
            page.goto(target_url or "about:blank")
            deadline = time.monotonic() + max(wait_seconds, 0)
            while time.monotonic() <= deadline:
                for index, item in enumerate(context.pages):
                    record_page("poll", item, index)
                if wait_seconds <= 0:
                    break
                time.sleep(1)
            context.close()

        detail = "Observed browser pages while user attempted ad center entry."
        status = "observed" if observed else "no_pages_observed"
        return AdCenterEntryCheckResult(status, detail, browser_executable, target_url, observed, popup_count)
    except Exception as error:  # noqa: BLE001
        return AdCenterEntryCheckResult("failed", str(error), browser_executable, target_url, observed, popup_count)
