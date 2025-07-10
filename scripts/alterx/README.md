
# 🔧 AlterX Wordlist Generator Pipeline

Цей скрипт на Python дозволяє автоматизувати генерацію словників субдоменів для пентесту на базі **apex-доменів**. Він комбінує можливості `subfinder` для збору відомих субдоменів та `alterx` для генерації варіацій (пермутацій).

---

## 📌 Що робить скрипт:

1. Читає список apex-доменів із `domains.txt`
2. Для кожного домену:
   - Збирає субдомени через `subfinder`
   - Генерує словники з мутаціями через `alterx` (стандартні + кастомні шаблони)
   - Об'єднує результат у фінальний файл `alterx_combined_<domain>.txt`
3. Продовжує обробку навіть при помилках

---

## 📂 Структура проєкту

```
.
├── domains.txt                         # Файл зі списком apex-доменів (наприклад: example.com)
├── alterx_pipeline.py                 # Основний Python-скрипт (вставити тут)
├── /usr/local/share/wordlists/
│   └── permutations/permutations_wordlist.txt  # Словник шаблонів для alterx
├── combined_wordlist_<domain>.txt     # Субдомени, зібрані subfinder
├── alterx_standard_<domain>.txt       # Пермутації (стандартні)
├── alterx_custom_<domain>.txt         # Пермутації (кастомні шаблони)
├── alterx_combined_<domain>.txt       # Фінальний згенерований словник
```

---

## ⚙️ Вимоги

- Python 3.6+
- Установлені CLI-утиліти:
  - [`subfinder`](https://github.com/projectdiscovery/subfinder)
  - [`alterx`](https://github.com/projectdiscovery/alterx)

---

## 📝 domains.txt — приклад

```
example.com
fuckrussia.ru
testdomain.org
```

---

## 📦 Словник шаблонів для alterx

Шлях за замовчуванням:
```
/usr/local/share/wordlists/permutations/permutations_wordlist.txt
```

📌 Приклад вмісту:

```
dev
test
admin
staging
api
v1
backup
```

---

## 🚀 Приклад запуску

```bash
python3 alterx_pipeline.py
```

Після виконання, ти отримаєш файл `alterx_combined_<domain>.txt` для кожного з доменів.

---
