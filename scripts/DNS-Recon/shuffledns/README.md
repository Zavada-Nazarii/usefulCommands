# 🛡️ Shuffledns Validator for Existing DNS Results

Цей інструмент дозволяє **валідувати зібрані доменні записи** (сабдомени) через `shuffledns`, використовуючи **trusted DNS resolvers**.  
Він **не виконує брутфорс**, а перевіряє, які з уже знайдених сабдоменів реально резолвляться.

---

## 🧩 Для чого цей скрипт?

Під час DNS-рекон (Recon) ти зазвичай проходиш кілька етапів:
- 🔸 `alterx`
- 🔸 `dnx resolve`
- 🔸 `puredns`
- 🔸 ... інші інструменти

Ці етапи генерують **великі обсяги сабдоменів**, з яких не всі обов'язково дійсні (живі DNS-записи).

🔍 Цей скрипт:
- Збирає **всі домени з результатів попередніх етапів**
- Видаляє дублікати
- Валідуює залишені записи через `shuffledns`
- Виводить лише ті, що **успішно резолвляться** в DNS

---

## 🛠️ Встановлення

1. Встанови `shuffledns`:

```bash
GO111MODULE=on go install -v github.com/projectdiscovery/shuffledns/cmd/shuffledns@latest
```

> Уважно: `~/.go/bin` має бути в `$PATH`, або перемістити `shuffledns` в `/usr/local/bin`

2. Встанови залежності Python:

```bash
pip install -r requirements.txt
```

> `requirements.txt` містить лише:
```
requests
```

---

## 📁 Структура директорій

```
project_folder/
├── dns_results/                  ← тут лежать результати alterx, puredns, dnxs тощо
│   ├── target1/
│   │   └── puredns.txt
│   └── target2/
│       └── alterx.txt
├── validate_with_shuffledns.py  ← головний скрипт
├── final_valid_hosts.txt        ← результат: 100% валідні хости
├── trickest-trusted.txt         ← завантажується автоматично
```

---

## 🚀 Запуск

```bash
python3 validate_with_shuffledns.py
```

Скрипт:
1. Рекурсивно пройде по `dns_results/`
2. Збере всі домени в `tmp_all_domains.txt`
3. Завантажить резолвери з GitHub (Trickest Trusted)
4. Проганяє через `shuffledns` (без брутфорсу)
5. Виведе результат у `final_valid_hosts.txt`

---

## 📌 Вхідні дані

- `dns_results/` — директорія з будь-якою глибиною вкладеності
- У кожному файлі мають бути домени (по одному на рядок)

**Приклад:**
```
mail.example.com
vpn.example.com
api.testsite.org
...
```

---

## 📤 Вихідні дані

- `final_valid_hosts.txt` — файл із усіма валідними хостами (після резолву)
- Усі результати відсортовані та без дублікатів

---

## 🔐 Примітки

- Скрипт **не генерує нових сабдоменів**, тільки валідує вже знайдені
- Ідеально підходить як фінальний етап після `alterx`, `dnxs`, `puredns`, `amass` тощо
- Для великих обсягів можна запускати з проксі або обмеженням по rate

---
