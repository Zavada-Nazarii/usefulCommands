import os
import subprocess
import requests
from pathlib import Path

# === Конфігурація ===
INPUT_DIR = "./dns_results"  # Шлях до папки з усіма результатами (рекурсивно)
TMP_DOMAINS_FILE = "./tmp_all_domains.txt"
VALID_OUTPUT_FILE = "./final_valid_hosts.txt"
RESOLVERS_FILE = "./trickest-trusted.txt"

TRICKEST_RESOLVERS_URL = "https://raw.githubusercontent.com/trickest/resolvers/main/resolvers-trusted.txt"

def download_resolvers():
    if not Path(RESOLVERS_FILE).exists():
        print("[*] Завантаження Trickest Trusted resolvers...")
        r = requests.get(TRICKEST_RESOLVERS_URL)
        if r.status_code == 200:
            with open(RESOLVERS_FILE, "w") as f:
                f.write(r.text)
            print("[+] Резолвери збережено.")
        else:
            raise Exception("[-] Неможливо завантажити резолвери з GitHub")

def collect_domains(directory):
    print(f"[*] Збір доменів із директорії: {directory}")
    domains = set()
    for path in Path(directory).rglob("*"):
        if path.is_file():
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    line = line.strip()
                    if line and "." in line:
                        domains.add(line.lower())
    print(f"[+] Зібрано {len(domains)} унікальних доменів.")
    return sorted(domains)

def save_to_file(lines, filepath):
    with open(filepath, "w") as f:
        for line in lines:
            f.write(line + "\n")

def run_shuffledns(input_file, output_file):
    cmd = (
        f"shuffledns -list {input_file} "
        f"-r {RESOLVERS_FILE} "
        f"-o {output_file} "
        f"-silent -sw -duc"
    )
    print("[*] Валідація доменів через shuffledns...")
    subprocess.run(cmd, shell=True, check=True)
    print(f"[+] Результати збережено в: {output_file}")

def main():
    download_resolvers()
    domains = collect_domains(INPUT_DIR)
    save_to_file(domains, TMP_DOMAINS_FILE)
    run_shuffledns(TMP_DOMAINS_FILE, VALID_OUTPUT_FILE)

if __name__ == "__main__":
    main()

