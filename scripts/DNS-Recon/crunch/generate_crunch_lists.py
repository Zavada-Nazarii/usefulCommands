import subprocess
from pathlib import Path

# === Налаштування ===
DOMAINS_FILE = "domains.txt"
CHARSET_FILE = "/usr/share/crunch/charset.lst"  # змінити шлях, якщо потрібно
OUTPUT_DIR = Path("crunch-generated")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# === Конфігурація завдань
CRUNCH_TASKS = [
    {
        "desc": "1-4 символи, lalpha-numeric-dash",
        "min_len": "1",
        "max_len": "4",
        "charset": "lalpha-numeric-dash"
    },
    {
        "desc": "5 символів, lalpha",
        "min_len": "5",
        "max_len": "5",
        "charset": "lalpha"
    }
    # Можна додати ще великі варіанти за потреби
]

def check_crunch():
    try:
        subprocess.run(["crunch", "--version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[+] crunch знайдено.")
    except FileNotFoundError:
        print("[!] crunch не знайдено. Встанови через:")
        print("    sudo apt install crunch")
        exit(1)

def run_crunch_task(task):
    print(f"[~] Генерація шаблону: {task['desc']}")
    try:
        result = subprocess.run([
            "crunch", task["min_len"], task["max_len"],
            "-f", CHARSET_FILE, task["charset"]
        ], capture_output=True, text=True, check=True)
        lines = result.stdout.strip().split("\n")
        print(f"[+] Отримано {len(lines)} шаблонів.")
        return lines
    except subprocess.CalledProcessError as e:
        print(f"[!] crunch помилка: {e}")
        return []

def generate_domain_subs(perms):
    if not Path(DOMAINS_FILE).is_file():
        print(f"[!] Не знайдено {DOMAINS_FILE}")
        return

    with open(DOMAINS_FILE, "r") as f:
        domains = [d.strip() for d in f if d.strip()]

    for domain in domains:
        outfile = OUTPUT_DIR / f"crunch_generated_{domain}.txt"
        with open(outfile, "a") as out:
            for p in perms:
                out.write(f"{p}.{domain}\n")
        print(f"[+] ✅ Додано для: {domain} ({len(perms)} записів)")

def main():
    check_crunch()
    for task in CRUNCH_TASKS:
        perms = run_crunch_task(task)
        if perms:
            generate_domain_subs(perms)

if __name__ == "__main__":
    main()
