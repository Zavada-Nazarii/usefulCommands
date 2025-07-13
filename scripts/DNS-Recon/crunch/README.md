# Crunch Subdomain Generator

Цей скрипт автоматизує генерацію можливих сабдоменів для вказаних доменів за допомогою утиліти [`crunch`](https://tools.kali.org/password-attacks/crunch), використовуючи визначені шаблони. Він створює словники, які можна використовувати у фазі **Subdomain Enumeration** у пентестах або багбаунті.

---

## 🧠 Для чого це потрібно?

Цей інструмент створює кастомні сабдомени з урахуванням символьних шаблонів (довжина, тип символів), наприклад:

```
a.example.com
abc1.example.com
test5.example.com
```

Може бути корисним:
- для атак типу **DNS bruteforce** (наприклад, пошук нестандартних внутрішніх сабдоменів);
- під час **перевірки захищеності DNS/WAF**;
- для генерації словників для інших тулів (alterx, puredns, shuffleDNS тощо).

---

## 🚀 Як запускати

1. Створи файл `domains.txt` з переліком доменів (по одному в рядку), наприклад:
```
example.com
testsite.org
```

2. Встанови crunch:
```bash
sudo apt install crunch
```

3. Запусти скрипт:
```bash
python3 generate_crunch_lists.py
```

---

## 🔧 Залежності

- `crunch`
- Python 3.x
- Файл `/usr/share/crunch/charset.lst` (типовий набір символів crunch)

---

## ⚙️ Що робить скрипт

1. Читає список доменів із `domains.txt`.
2. Для кожного шаблону (визначено в `CRUNCH_TASKS`) запускає crunch.
3. Генерує сабдомени виду `XXX.domain.com`, де `XXX` — згенерований шаблон.
4. Результат зберігається у `crunch-generated/crunch_generated_<домен>.txt`.

---

## 📂 Структура файлів

```
.
├── crunch_subgen.py
├── domains.txt
├── crunch-generated/
│   ├── crunch_generated_example.com.txt
│   └── ...
```
---
