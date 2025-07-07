# 🔍 Пошук згадок `mail` у JSON-файлі та очистка лапок

Цей файл описує процес пошуку всіх згадок про `mail` у JSON-файлі, фільтрацію об’єктів, що містять це слово, та видалення лапок із знайдених доменів.

---

## 📁 Вхідні дані

Файл у форматі JSON — наприклад:

```json
[
  { "id": 1, "email": "user1@mail.anozit.ru", "name": "User One" },
  { "id": 2, "email": "user2@site.com", "name": "User Two" },
  { "id": 3, "username": "mailman", "name": "Mail Man" }
]
```

---

## ✅ Витяг елементів, що містять `mail`, за допомогою `jq`

### Якщо JSON — масив об'єктів:

```bash
cat file.json | jq '.[] | select(tostring | test("mail"))'
```

### Якщо структура складніша або це просто об'єкт:

```bash
cat file.json | jq 'select(tostring | test("mail"))'
```

### Якщо потрібно знайти всі рядки з `mail` (включно з вкладеними полями):

```bash
cat file.json | jq '.. | select(type == "string" and test("mail"))'
```

### Якщо потрібно знайти всі рядки з `title` (без title, лише значення і передами рядками через кому):

```bash
cat file.json | jq -r '.. | objects | .title? // empty' | sed 's/$/,/'
```

---

## 🧼 Видалення лапок із результатів

### За допомогою `grep` + `tr`:

```bash
cat file.json | grep -oE '"mail[^"]+"' | tr -d '"'
```

### Альтернатива через `sed`:

```bash
cat file.json | grep -oE '"mail[^"]+"' | sed 's/"//g'
```

### Або комбіновано:

```bash
sed -n 's/.*"\(mail[^"]*\)".*/\1/p' file.json
```

---

## 🛠 Зауваження

- Якщо `jq` не встановлено:

### Для Ubuntu/Debian:

```bash
sudo apt install jq
```

### Для MacOS:

```bash
brew install jq
```

---

## 📌 Підсумок

| Метод         | Команда                                                                 |
|---------------|-------------------------------------------------------------------------|
| `grep + tr`   | `cat file | grep -oE '"mail[^"]+"' | tr -d '"'`                         |
| `jq`          | `cat file | jq -r '.. | select(type == "string") | select(test("mail"))'` |
| `sed`         | `sed 's/"//g'` або `sed -n ...`                                         |

---
