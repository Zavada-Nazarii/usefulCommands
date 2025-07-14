import subprocess
from pathlib import Path
import argparse

# === Налаштування ===
INPUT_DIR = Path("crunch-generated")
OUTPUT_DIR = Path("domain-verified")
RESOLVERS_FILE = Path("resolvers.txt")  # Змінити шлях, якщо потрібно

# === Підготовка ===
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def check_puredns():
    try:
        subprocess.run(["puredns", "--help"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("[+] puredns знайдено.")
    except FileNotFoundError:
        print("[!] puredns не встановлено. Встанови через:")
        print("    go install github.com/d3mondev/puredns/v2@latest")
        exit(1)

def process_files(use_local_dns: bool):
    txt_files = list(INPUT_DIR.rglob("crunch_generated_*"))
    if not txt_files:
        print("[!] Не знайдено *_resolved.txt у папці domain-resolved")
        return

    for file in txt_files:
        relative_subpath = file.parent.relative_to(INPUT_DIR)
        target_subdir = OUTPUT_DIR / relative_subpath
        target_subdir.mkdir(parents=True, exist_ok=True)

        out_file = target_subdir / file.name.replace("_resolved.txt", "_verified.txt")

        print(f"[~] Обробка: {file}")
        if use_local_dns:
            # Локальний резолвер 127.0.0.1
            cmd = [
                "puredns", "resolve", str(file),
                "--resolvers", "/dev/stdin",
                "--write", str(out_file)
            ]
            print("    [*] Використовується локальний DNS: 127.0.0.1")
            try:
                subprocess.run(cmd, input=b"127.0.0.1\n", check=True)
            except subprocess.CalledProcessError as e:
                print(f"[!] ❌ Помилка puredns на {file.name}: {e}")
        else:
            # Використання resolvers.txt
            cmd = [
                "puredns", "resolve", str(file),
                "--resolvers", str(RESOLVERS_FILE),
                "--write", str(out_file)
            ]
            try:
                subprocess.run(cmd, check=True)
                print(f"[+] ✅ Збережено: {out_file}")
            except subprocess.CalledProcessError as e:
                print(f"[!] ❌ Помилка puredns на {file.name}: {e}")

def main():
    parser = argparse.ArgumentParser(description="Batch Puredns Resolver")
    parser.add_argument("--local", action="store_true", help="Використовувати локальний DNS (127.0.0.1)")
    args = parser.parse_args()

    check_puredns()
    process_files(use_local_dns=args.local)

if __name__ == "__main__":
    main()

