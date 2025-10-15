import ipaddress
import socket
import sys

# Налаштування
CIDR_FILE = 'cidr_targets.txt'  # Файл, що містить CIDR-блоки (наприклад, 153.46.176.0/22)
OUTPUT_FILE = 'resolved_domains.txt' # Файл для збереження знайдених доменів

def resolve_ip_to_hostname(ip_address):
    """Виконує зворотний пошук DNS для даної IP-адреси."""
    try:
        # socket.gethostbyaddr(ip) повертає кортеж: (hostname, aliaslist, iplist)
        hostname, _, _ = socket.gethostbyaddr(ip_address)
        return hostname
    except socket.error:
        # Якщо PTR-запис не знайдено, або виникла інша помилка мережі
        return None

def process_cidrs_and_resolve(cidr_file, output_file):
    """
    Читає CIDR-блоки, розгортає їх у IP-адреси,
    виконує зворотний пошук та зберігає домени.
    """
    total_ips = 0
    resolved_count = 0
    resolved_domains = set()

    print(f"Починаємо обробку CIDR-блоків із файлу: {cidr_file}...")

    try:
        with open(cidr_file, 'r') as f:
            cidrs = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Помилка: Файл {cidr_file} не знайдено.")
        return

    for cidr in cidrs:
        try:
            net = ipaddress.ip_network(cidr, strict=False)
            
            # Обробка перших та останніх адрес (мережевий ID та широкомовний адрес)
            # може бути пропущена для більшості випадків
            for ip in net.hosts():
                ip_str = str(ip)
                total_ips += 1
                
                # Обмеження для великих блоків:
                if total_ips % 100 == 0:
                    sys.stdout.write(f"\rОбробка IP: {ip_str} | Всього перевірено: {total_ips} | Знайдено доменів: {resolved_count}")
                    sys.stdout.flush()

                domain = resolve_ip_to_hostname(ip_str)
                
                if domain:
                    if domain not in resolved_domains:
                        resolved_domains.add(domain)
                        resolved_count += 1
                        
        except ValueError as e:
            print(f"\nПомилка при обробці CIDR '{cidr}': {e}")
            continue

    sys.stdout.write(f"\rОбробка завершена. Всього перевірено IP: {total_ips} | Знайдено доменів: {resolved_count}\n")
    
    # Збереження результатів
    if resolved_domains:
        with open(output_file, 'w') as out_f:
            for domain in sorted(list(resolved_domains)):
                out_f.write(f"{domain}\n")
        print(f"✅ Знайдені домени ({resolved_count}) збережено у файл: {output_file}")
    else:
        print("❌ Доменних імен не знайдено.")

if __name__ == "__main__":
    process_cidrs_and_resolve(CIDR_FILE, OUTPUT_FILE)
