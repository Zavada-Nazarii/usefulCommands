# ✅ Puredns Validation Pipeline

Цей репозиторій/папка містить інструменти для **точної валідації сабдоменів** після генерації/ресолвінгу з використанням `puredns`.

Запускати після [dnsx](https://github.com/Zavada-Nazarii/usefulCommands/tree/master/scripts/DNS-Recon/DNS_trickest_resolvers)

---

## 🔧 Необхідні інструменти

### 1. Встановлення `massdns`

```bash
git clone https://github.com/blechschmidt/massdns.git
cd massdns
make
sudo cp bin/massdns /usr/local/bin/
```

### 2. Встановлення `puredns`

```bash
go install github.com/d3mondev/puredns/v2@latest
```

Перевірка:

```bash
puredns --help
```

---

## 📁 Структура директорій

```
.
├── domain-resolved/                # Вхідні результати (dnsx/alterx)
│   ├── standard/
│   ├── custom/
│   └── combined/
│       └── example.com_resolved.txt
├── domain-verified/                # Вихідні перевірені сабдомени
├── resolvers.txt                   # Список DNS-резолверів
├── puredns_verify_recursive.py     # Скрипт валідації
```

---

## 🚀 Запуск валідації

```bash
python3 puredns_verify_recursive.py           # через resolvers.txt
python3 puredns_verify_recursive.py --local   # через локальний DNS (127.0.0.1)
```

> Вибір `--local` дозволяє резолвити потужно і без rate-limit/блокувань

---

## 🪠 Чому варто використовувати локальний DNS (Unbound)

| Перевага              | Пояснення                                  |
| --------------------- | ------------------------------------------ |
| 🚀 Швидкість          | Кеш, місцевий рекурсивний DNS              |
| 🚫 Ніяких rate-limit  | Ні VPS cloud, ні Google DNS тебе не забанять |
| 🔐 Більша точність    | Відсутні wildcard-відповіді від CDN        |
| 🌐 DNSSEC/Prefetching | Можна контролювати TTL/кеш/сервери         |

---

## 🔨 Встановлення Unbound DNS

```bash
sudo apt update && sudo apt install unbound -y
```

### Створити root hints

```bash
sudo curl -o /var/lib/unbound/root.hints https://www.internic.net/domain/named.cache
```

### Створити конфіг `/etc/unbound/unbound.conf`

```conf
server:
  verbosity: 1
  interface: 127.0.0.1
  access-control: 127.0.0.1/8 allow

  # Продуктивність
  num-threads: 4
  msg-cache-size: 100m
  rrset-cache-size: 100m
  cache-min-ttl: 300
  cache-max-ttl: 86400
  prefetch: yes
  prefetch-key: yes

  # IPv6 можна вимкнути, якщо не потрібен
  do-ip6: no

  # Обмеження
  do-not-query-localhost: no

  # Збільшення лімітів
  outgoing-range: 8192
  num-queries-per-thread: 4096
  so-rcvbuf: 4m
  so-sndbuf: 4m

  # Рекурсія напряму до root DNS
  harden-glue: yes
  harden-dnssec-stripped: yes
  unwanted-reply-threshold: 10000000
  module-config: "iterator"
# Root hints (авторитетні root-сервери)
root-hints: "/var/lib/unbound/root.hints"
```

### Перевірка і запуск

```bash
sudo unbound-checkconf
sudo systemctl restart unbound
```

### Тест DNS

```bash
dig example.com @127.0.0.1 +short
```

---

## 🧪 Типові проблеми

- `trust anchor presented twice` — вимкни DNSSEC або знову згенеруй root.key
- `--bin` не працює — сучасні версії puredns його видалили
- "cloud VPS" буває блокує DNS за 8.8.8.8 — локальний днс це байпас

---

## 🪜 Порядок дій

1. Встанови Unbound
2. Створи root.hints
3. Вставь конфіг (module-config: "iterator")
4. `dig example.com @127.0.0.1`
5. `python3 puredns_verify_recursive.py --local`

---

## 🧩 Рекомендований порядок етапів

| Етап | Інструмент | Призначення |
|------|------------|-------------|
| 1️⃣  | `alterx`, `crunch`, `gotator` | Генерація сабдоменів |
| 2️⃣  | `dnsx` | Масове фільтрування (опційно) |
| 3️⃣  | `puredns` | Точна перевірка, фільтр wildcard |
| 4️⃣  | `httpx`, `nuclei` | Веб/сканування активів |

---

## 📌 Команди прикладу

```bash
# Приклад запуску puredns вручну
puredns resolve domain-resolved/standard/example.com_resolved.txt \
  --resolvers resolvers.txt \
  --write domain-verified/standard/example.com_verified.txt
```

---

## 📥 Формат файлів

- Вхідні: `*_resolved.txt` — по одному сабдомену на рядок
- Вихідні: `*_verified.txt` — лише валідні, нефальшиві сабдомени

---

## 🧪 Перевірка resolver'ів (опційно)

```bash
puredns resolve test.txt --resolvers resolvers.txt --write /dev/null
```
---

