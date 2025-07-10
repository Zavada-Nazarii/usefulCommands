# ✅ Puredns Validation Pipeline

Цей репозиторій/папка містить інструменти для **точної валідації сабдоменів** після генерації/ресолвінгу з використанням `puredns`.

ЗАпускати після [dnsx](https://github.com/Zavada-Nazarii/usefulCommands/tree/master/scripts/DNS_trickest_resolvers)

---

## 🔧 Необхідні інструменти

### 1. Встановлення `massdns`

`puredns` використовує `massdns` для високошвидкісного DNS-резолвінгу:

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
├── domain-resolved/                # Вхідні результати (від alterx/dnsx)
│   ├── standard/
│   ├── custom/
│   └── combined/
│       └── example.com_resolved.txt
├── domain-verified/                # Вихідні перевірені дані
│   └── ...
├── resolvers.txt                   # Список DNS-релолверів
├── puredns_verify_recursive.py     # Скрипт валідації
```

---

## 🚀 Запуск валідації

```bash
python3 puredns_verify_recursive.py
```

Цей скрипт:
- сканує всі `*_resolved.txt` файли в `domain-resolved/**`
- перевіряє через `puredns`
- створює `*_verified.txt` в `domain-verified/**`

> ⚠️ Вимагає файл `resolvers.txt` з валідними DNS (1 на рядок, напр. `1.1.1.1`)

---

## 🧠 Взаємодія з іншими інструментами

### 📍 `dnsx` — масовий фільтр

- Використовується для попереднього фільтрування великих словників
- Дає швидкий `A/AAAA`-результат, але **може включати wildcard-и**
- Підходить для грубого скорочення словника

### 🧪 `puredns` — точна валідація

- Виявляє wildcard-домени
- Видаляє false-positives
- Дає **еталонний набір живих сабдоменів**

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
