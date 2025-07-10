import subprocess
import os
from pathlib import Path
import re
import urllib.request
from collections import defaultdict

# === Конфігурація ===
SCRIPT_DIR = Path(__file__).resolve().parent
INPUT_DIR = Path("alterex")
CRUNCH_DIR = Path("crunch")
RESOLVERS_URL = "https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt"
RESOLVERS_FILE = SCRIPT_DIR / "resolvers.txt"
OUTPUT_BASE = SCRIPT_DIR / "domain-resolved"

FILE_TYPES = {
    "standard": "alterx_standard_{}.txt",
    "custom": "alterx_custom_{}.txt",
    "combined": "alterx_combined_{}.txt",
    "crunch": "crunch_generated_{}.txt"
}

DNSX_CMD = "dnsx"

def download_resolvers():
    if RESOLVERS_FILE.exists() and RESOLVERS_FILE.stat().st_size > 0:
        print(f"[i] resolvers.txt вже існує.")
        return
    print(f"[+] Завантаження resolvers.txt з GitHub...")
    try:
        urllib.request.urlretrieve(RESOLVERS_URL, RESOLVERS_FILE)
        print(f"[+] ✅ Завантажено: {RESOLVERS_FILE}")
    except Exception as e:
        print(f"[!] ❌ Помилка при завантаженні resolvers.txt: {e}")
        exit(1)

def run_cmd(command):
    try:
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"[!] Помилка: {' '.join(command)}")
            print(f"    STDERR: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"[!] Виняток при виконанні команди: {e}")
        return None

def resolve_file(domain, type_name, input_path):
    output_dir = OUTPUT_BASE / type_name
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / f"{domain}_resolved.txt"

    print(f"[*] Обробка: {input_path.name} ({type_name})")

    command = [
        DNSX_CMD,
        "-l", str(input_path),
        "-r", str(RESOLVERS_FILE),
        "-a",
        "-silent",
        "-o", str(output_file)
    ]
    run_cmd(command)

    count = 0
    if output_file.exists():
        with open(output_file, "r") as f:
            count = sum(1 for _ in f)
    print(f"    [+] ✅ {count} валідних записів збережено у: {output_file.name}")
    return count

def find_domains():
    all_files = list(INPUT_DIR.glob("alterx_*_*.txt")) + list(CRUNCH_DIR.glob("crunch_generated_*.txt"))
    domain_set = set()

    pattern = re.compile(r"(?:alterx_(?:standard|custom|combined)|crunch_generated)_(.+)\.txt")
    for f in all_files:
        match = pattern.match(f.name)
        if match:
            domain_set.add(match.group(1))

    return sorted(domain_set)

def main():
    download_resolvers()
    stats = defaultdict(dict)

    domains = find_domains()
    if not domains:
        print("[!] ⚠️ Увага: не знайдено жодного файлу, але скрипт продовжує роботу.")
    else:
        print(f"[i] Знайдено {len(domains)} домен(ів) для обробки.")

    for domain in domains:
        print(f"\n=== 🔍 ДОМЕН: {domain} ===")
        for type_name, filename_pattern in FILE_TYPES.items():
            folder = CRUNCH_DIR if type_name == "crunch" else INPUT_DIR
            input_path = folder / filename_pattern.format(domain)
            if input_path.exists() and input_path.stat().st_size > 0:
                count = resolve_file(domain, type_name, input_path)
                stats[domain][type_name] = count
            else:
                print(f"[!] Пропускаю {type_name}: файл не знайдено або порожній.")

    # === ПІДСУМОК ===
    if stats:
        print("\n📊 === ПІДСУМКОВА СТАТИСТИКА ===")
        for domain in domains:
            total = 0
            print(f"\n{domain}:")
            for t in FILE_TYPES:
                count = stats[domain].get(t, 0)
                total += count
                print(f"  └─ {t:8s}: {count}")
            print(f"  ▶️ Всього: {total}")
    else:
        print("[i] Підсумкова статистика відсутня — не було оброблено жодного файлу.")

if __name__ == "__main__":
    main()

