import subprocess
from pathlib import Path

# === Налаштування ===
INPUT_DIR = Path("domain-resolved")
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

def process_files():
    txt_files = list(INPUT_DIR.rglob("*_resolved.txt"))
    if not txt_files:
        print("[!] Не знайдено *_resolved.txt у папці domain-resolved")
        return

    for file in txt_files:
        relative_subpath = file.parent.relative_to(INPUT_DIR)
        target_subdir = OUTPUT_DIR / relative_subpath
        target_subdir.mkdir(parents=True, exist_ok=True)

        out_file = target_subdir / file.name.replace("_resolved.txt", "_verified.txt")

        print(f"[~] Обробка: {file}")
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
    check_puredns()
    process_files()

if __name__ == "__main__":
    main()
