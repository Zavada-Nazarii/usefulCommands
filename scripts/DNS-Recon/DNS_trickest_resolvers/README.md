# 🧠 DNS Permutation + Validation Pipeline

Цей проєкт реалізує повноцінний пайплайн для DNS-пермутацій, валідації та резолвінгу сабдоменів з використанням `alterx`, `subfinder`, `dnsx`, та `trickest/resolvers`.

ЗАпускати після [alterx](https://github.com/Zavada-Nazarii/usefulCommands/blob/master/scripts/alterx/README.md)

---

## 📦 Використані інструменти

- [`alterx`](https://github.com/projectdiscovery/alterx) — генерація сабдоменів за шаблонами.
- [`subfinder`](https://github.com/projectdiscovery/subfinder) — пасивне збирання сабдоменів.
- [`dnsx`](https://github.com/projectdiscovery/dnsx) — DNS resolution для масивів доменів.
- [`resolvers.txt`](https://github.com/trickest/resolvers) — список валідних open DNS resolvers.

---

## ⚙️ Структура пайплайну

1. **Збір початкових сабдоменів**:
    ```bash
    subfinder -silent -d example.com -o combined_wordlist_example.com.txt
    ```

2. **Генерація пермутацій (standard/custom)**:
    ```bash
    alterx -enrich -l combined_wordlist_example.com.txt -o alterx_standard_example.com.txt
    alterx -enrich -l combined_wordlist_example.com.txt -pp word=/path/to/permutations_wordlist.txt -o alterx_custom_example.com.txt
    ```

3. **Об’єднання результатів**:
    Скрипт автоматично об’єднує standard + custom у:
    ```
    alterx_combined_example.com.txt
    ```

---

## 🚀 Резолвінг через `dnsx`

### Встановлення `dnsx`:
```bash
go install -v github.com/projectdiscovery/dnsx/cmd/dnsx@latest
echo 'export PATH=$PATH:$HOME/go/bin' >> ~/.bashrc
source ~/.bashrc
```

### Приклад команди:
```bash
dnsx -l alterx_combined_example.com.txt -r resolvers.txt -a -silent -o example.com_resolved.txt
```

---

## 📂 Структура директорій

- `alterx-files/` — папка з усіма alterx_* файлами.
- `domain-resolved/`
    - `standard/`
    - `custom/`
    - `combined/`

---

## 🧰 Автоматизований скрипт

```bash
python3 resolve_all_mutations.py
```

Він:
- Завантажує `resolvers.txt`, якщо відсутній;
- Обробляє всі `alterx_*_{domain}.txt`;
- Зберігає валідні результати у відповідні директорії;
- Виводить статистику.

---

## 📥 Завантаження resolvers.txt (автоматично, або вручну):
```bash
wget https://raw.githubusercontent.com/trickest/resolvers/main/resolvers.txt
```

---

## 📊 Вивід результатів

Файли типу:
```
domain-resolved/standard/example.com_resolved.txt
domain-resolved/custom/example.com_resolved.txt
domain-resolved/combined/example.com_resolved.txt
```

Містять лише ті сабдомени, які успішно резольвились.

---

