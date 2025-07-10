import subprocess
import os
from pathlib import Path

# Налаштування
DOMAINS_FILE = "domains.txt"
PERMUTATION_WORDLIST = "/usr/local/share/wordlists/permutations/permutations_wordlist.txt"

def run_cmd(command, shell=False):
    try:
        result = subprocess.run(command, shell=shell, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"[!] Помилка при виконанні команди: {' '.join(command)}")
            print(f"    STDERR: {result.stderr.strip()}")
            return None
        return result.stdout.strip()
    except Exception as e:
        print(f"[!] Виняток під час запуску: {e}")
        return None

def process_domain(domain):
    domain = domain.strip()
    if not domain:
        return

    print(f"\n[*] Обробка домену: {domain}")
    base_wordlist = f"combined_wordlist_{domain}.txt"
    out_standard = f"alterx_standard_{domain}.txt"
    out_custom = f"alterx_custom_{domain}.txt"
    out_final = f"alterx_combined_{domain}.txt"

    # 1. subfinder
    print("    [+] Запуск subfinder...")
    subfinder_output = run_cmd(["subfinder", "-silent", "-d", domain, "-o", base_wordlist])
    if not Path(base_wordlist).is_file() or os.stat(base_wordlist).st_size == 0:
        print("    [!] Нічого не знайдено. Пропускаю.")
        return

    # 2. alterx стандартний
    print("    [+] alterx (standard)...")
    run_cmd(["alterx", "-enrich", "-l", base_wordlist, "-o", out_standard])

    # 3. alterx кастомні шаблони
    print("    [+] alterx (custom)...")
    run_cmd(["alterx", "-enrich", "-l", base_wordlist, "-pp", f"word={PERMUTATION_WORDLIST}", "-o", out_custom])

    # 4. Об'єднання результатів
    print("    [+] Об'єднання результатів...")
    combined_set = set()
    for file in [out_standard, out_custom]:
        if Path(file).is_file():
            with open(file, "r") as f:
                combined_set.update(line.strip() for line in f if line.strip())

    if combined_set:
        with open(out_final, "w") as out:
            for line in sorted(combined_set):
                out.write(f"{line}\n")
        print(f"    [+] ✅ Створено: {out_final}")
    else:
        print(f"    [!] ❌ Порожній результат для {domain}")

def main():
    if not Path(DOMAINS_FILE).is_file():
        print(f"[!] Не знайдено файл: {DOMAINS_FILE}")
        return
    if not Path(PERMUTATION_WORDLIST).is_file():
        print(f"[!] Не знайдено словник пермутацій: {PERMUTATION_WORDLIST}")
        return

    with open(DOMAINS_FILE, "r") as f:
        domains = f.readlines()

    for domain in domains:
        process_domain(domain)

if __name__ == "__main__":
    main()

