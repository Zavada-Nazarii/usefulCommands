import subprocess
from pathlib import Path
import tldextract
import argparse

# === Шляхи ===
DOMAINS_FILE = "domains.txt"  # список доменів
WORDLIST_FILE = Path("/usr/local/share/crunch/crunch_1_4_lalpha-numeric-dash.txt")
OUTPUT_DIR = Path("subdomains")
RESOLVERS_FILE = Path("resolvers.txt")

# === Підготовка ===
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def check_requirements():
    try:
        subprocess.run(["puredns", "--help"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print("[+] puredns знайдено.")
    except FileNotFoundError:
        print("[!] puredns не встановлено. Встанови через:")
        print("    go install github.com/d3mondev/puredns/v2@latest")
        exit(1)

    if not WORDLIST_FILE.is_file():
        print(f"[!] Не знайдено словник: {WORDLIST_FILE}")
        exit(1)

def get_apex_domains():
    if not Path(DOMAINS_FILE).is_file():
        print(f"[!] Не знайдено {DOMAINS_FILE}")
        exit(1)

    with open(DOMAINS_FILE, "r") as f:
        domains = [line.strip() for line in f if line.strip()]
    return domains

def generate_subs(domain: str):
    print(f"[~] Генерація сабдоменів для: {domain}")
    temp_file = Path(f"/tmp/tmp_crunch_{domain.replace('.', '_')}.txt")

    with open(WORDLIST_FILE, "r") as wl, open(temp_file, "w") as out:
        for line in wl:
            sub = line.strip()
            if sub:
                out.write(f"{sub}.{domain}\n")
    return temp_file

def resolve_subdomains(domain: str, sub_file: Path, use_local_dns: bool):
    extracted = tldextract.extract(domain)
    domain_suffix = f"{extracted.domain}.{extracted.suffix}"
    out_name = f"crunch_generated_14_{domain_suffix}.txt"
    out_path = OUTPUT_DIR / out_name

    if use_local_dns:
        cmd = [
            "puredns", "resolve", str(sub_file),
            "--resolvers", "/dev/stdin",
            "--write", str(out_path)
        ]
        print("    [*] Використовується локальний DNS: 127.0.0.1")
        try:
            subprocess.run(cmd, input=b"127.0.0.1\n", check=True)
            print(f"[+] ✅ Збережено: {out_path}")
        except subprocess.CalledProcessError as e:
            print(f"[!] ❌ Помилка puredns для {domain}: {e}")
    else:
        cmd = [
            "puredns", "resolve", str(sub_file),
            "--resolvers", str(RESOLVERS_FILE),
            "--write", str(out_path)
        ]
        try:
            subprocess.run(cmd, check=True)
            print(f"[+] ✅ Збережено: {out_path}")
        except subprocess.CalledProcessError as e:
            print(f"[!] ❌ Помилка puredns для {domain}: {e}")

    sub_file.unlink()  # очищення тимчасового файлу

def main():
    parser = argparse.ArgumentParser(description="Puredns Resolver з crunch словником")
    parser.add_argument("--local", action="store_true", help="Використовувати локальний DNS (127.0.0.1)")
    args = parser.parse_args()

    check_requirements()
    domains = get_apex_domains()

    for domain in domains:
        temp_sub_file = generate_subs(domain)
        resolve_subdomains(domain, temp_sub_file, use_local_dns=args.local)

if __name__ == "__main__":
    main()

