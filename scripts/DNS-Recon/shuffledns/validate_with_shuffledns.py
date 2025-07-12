import os
import subprocess
import requests
from pathlib import Path

# === Конфігурація ===
INPUT_DIR = "/puredns/domain-verified"
OUTPUT_DIR = "./validated"
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

def run_shuffledns_per_file(input_path: Path, output_path: Path):
    cmd = (
        f"shuffledns -list \"{input_path}\" "
        f"-r {RESOLVERS_FILE} "
        f"-o \"{output_path}\" "
        f"-silent -sw -duc -mode resolve"
    )
    print(f"[*] Валідація без wildcard: {input_path.name}")
    try:
        subprocess.run(cmd, shell=True, check=True)
        print(f"[+] Готово: {output_path.name}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Помилка у {input_path.name}: {e}")

def main():
    download_resolvers()
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for path in Path(INPUT_DIR).rglob("*.txt"):
        if path.is_file():
            output_filename = f"shuffledns_{path.stem}.txt"
            output_path = Path(OUTPUT_DIR) / output_filename
            run_shuffledns_per_file(path, output_path)

if __name__ == "__main__":
    main()

