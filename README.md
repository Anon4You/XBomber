<div align="center">

<img src="assets/banner.png" alt="XBomber Banner" width="220">

<br/>

# XBomber

**High-Performance SMS Gateway Testing Tool**

<br/>

[![Python](https://img.shields.io/badge/Python-3.10+-yellow?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Platform](https://img.shields.io/badge/Platform-Termux%20%7C%20Linux%20%7C%20macOS-blue?style=for-the-badge&logo=linux&logoColor=white)](https://termux.com)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](LICENSE)
[![Version](https://img.shields.io/badge/Version-3.0.0-purple?style=for-the-badge)](CHANGELOG.md)

<br/>

*A structured, extensible tool for testing SMS gateway resilience —*  
*built with clean Python architecture and a Rich-powered terminal UI.*

</div>

---

> [!WARNING]
> **For authorized testing only.** Using this tool against any number without explicit consent from the owner is illegal under the Information Technology Act and equivalent laws in most jurisdictions. The developer assumes zero liability for misuse. By running this software, you accept full responsibility for compliance with your local laws.

---

## Overview

XBomber stress-tests SMS OTP gateways by cycling through a configurable list of service endpoints. It is designed for security researchers and developers who need to verify that their own platforms handle request flooding correctly — rate limiting, OTP invalidation, and abuse detection.

Version 3.0.0 is a complete architectural rewrite over v2. It introduces typed data models, persistent per-thread HTTP sessions, proxy health tracking, DNS pre-validation, and granular per-error reporting — all driven by a single `services.json` config file.

---

## Features

- Thread-pool concurrency with a configurable worker count
- Persistent `requests.Session` per thread — connection reuse via HTTP keep-alive
- Automatic retry with exponential backoff on 5xx and 429 responses
- Proxy rotation with health scoring — failing proxies are down-weighted automatically
- DNS pre-validation — dead domains are skipped before a connection is attempted
- Per-request error classification — timeout, SSL, DNS, proxy, remote disconnect
- Live Rich progress bar with count, percentage, elapsed time, and ETA
- Post-run report: success rate, throughput (req/s), per-service breakdown
- Zero shell injection — banner and all output rendered natively via Rich
- Cross-platform URL opening — `xdg-open` → `open` → `webbrowser` fallback chain
- `services.json` hot-reload cache — config parsed once per process

---

## Requirements

| Requirement | Version |
|---|---|
| Python | 3.10 or later |
| pip packages | `rich`, `requests`, `urllib3` |
| OS | Termux (Android), Linux, macOS, Windows |

Termux users: install from [F-Droid](https://f-droid.org/en/packages/com.termux/) — the Play Store build has restricted background execution.

---

## Installation

### From Source

```bash
# 1. Update packages and install Python (Termux)
pkg update && pkg upgrade -y
pkg install python git -y

# 2. Clone the repository
git clone https://github.com/Anon4You/XBomber.git
cd XBomber

# 3. Install dependencies
pip install -r requirements.txt

# 4. Make executable
chmod +x xbomber.py
```

### From Termux Void Repo

> [!NOTE]
> Requires the [Termux Void Repo](https://termuxvoid.github.io/) to be added to your sources first.

```bash
apt install xbomber -y
```

---

## Usage

```bash
python xbomber.py
```

On first launch you will see the main menu:

```
  1. Start Bombing
  2. Protect My Number
  3. About / Services
  4. Exit
```

Select **1**, enter the 10-digit target number (without country code), set the message count and optionally adjust the thread count. The tool runs the session and prints a full report when done.

---

## Configuration

All service endpoints live in `assets/services.json`. The schema:

```json
{
  "services": [
    {
      "name":         "ServiceName",
      "url":          "https://api.example.com/otp?phone={phone}",
      "method":       "POST",
      "phone_format": "with_plus91",
      "encoding":     "json",
      "headers": {
        "Content-Type": "application/json"
      },
      "data": {
        "mobile": "{phone}"
      }
    }
  ]
}
```

| Field | Required | Values | Description |
|---|---|---|---|
| `name` | Yes | any string | Display name shown in reports |
| `url` | Yes | URL with optional `{phone}` | Endpoint to hit |
| `method` | No | `GET` `POST` `PUT` `PATCH` | Default: `POST` |
| `phone_format` | No | `raw` `with_plus91` `91` `91-` | How `{phone}` is interpolated |
| `encoding` | No | `json` `form` | Body encoding. Default: `json` |
| `headers` | No | object | Request headers |
| `data` | No | object or null | Request body. Use `{phone}` as placeholder |

Invalid entries are skipped with a warning — they do not crash the load.

### Proxy Support

To route traffic through proxies, populate the `PROXIES` list near the top of `xbomber.py`:

```python
PROXIES = [
    "http://user:pass@ip:port",
    "http://ip:port",
]
```

When empty (the default), all requests go direct. The health-scoring system automatically deprioritizes proxies that fail and re-introduces them as they recover.

---

## Project Structure

```
XBomber/
├── xbomber.py          # Main script
├── assets/
│   ├── services.json   # Service endpoint definitions
│   └── banner.png      # Banner image (README only)
├── requirements.txt
├── LICENSE
└── README.md
```

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a full history of changes across versions.

---

## License

Released under the [MIT License](LICENSE). You are free to use, modify, and distribute this software. Attribution appreciated but not required.

---

<div align="center">

Developed by [Anon4You](https://github.com/Anon4You)  
Telegram — [t.me/nullxvoid](https://t.me/nullxvoid)

</div>
