# Mobile Testing ADB Commands — example (test environment)

> Файл містить всі `adb` / локальні командні приклади, які ми використовували під час тестування. Кожна команда має коротке пояснення, для чого її застосовували.

---

## Загальні примітки
- Перед виконанням команд переконайтеся, що емулятор або пристрій підключений і `adb devices` показує ваш девайс.
- Багато команд вимагають `root` або `run-as` для доступу до sandbox-папки застосунку. У Genymotion root зазвичай доступний.
- Використовуйте лише у тестовому/дозволеному середовищі.

---

## Базові перевірки / інформація
```bash
adb devices
adb root
adb remount
adb shell getprop ro.product.model
adb shell getprop ro.product.brand
adb shell getprop ro.product.manufacturer
adb shell getprop ro.build.fingerprint
```

**Навіщо:** загальна діагностика емулятора/пристрою та перевірка змінених `build.prop` властивостей.

---

## Робота із build.prop (перекрасити емульований пристрій)
```bash
adb root
adb remount
adb pull /system/build.prop ./build.prop.geny.bak
# Відредагувати локальний ./build.prop, потім:
adb remount
adb push ./build.prop /system/build.prop
adb shell chmod 644 /system/build.prop
adb shell sync
adb reboot
```

**Навіщо:** змінювали `ro.product.model`, `ro.product.brand`, `ro.build.fingerprint` щоб емулятор не детектувався як Genymotion.

---

## Інсталяція ARM Translation / GApps / WebView / Chrome
```bash
# Drag-and-drop zip архівів Genymotion-ARM-Translation та OpenGApps у вікно Genymotion
adb install -r AndroidSystemWebView.apk
adb install -r com.android.chrome.apk
adb shell pm list packages | grep webview
adb shell pm path com.google.android.webview
```

**Навіщо:** щоб WebView мав потрібні native-бібліотеки і працював коректно у Android 9.

---

## Керування WebView sandbox (вирішення зависань)
```bash
adb root
adb shell setprop persist.webview.disable_sandbox 1
adb shell setprop persist.webview.multiprocess false
adb reboot
adb shell getprop persist.webview.disable_sandbox
adb shell getprop persist.webview.multiprocess
```

**Навіщо:** у деяких Genymotion образах WebView sandbox не стартує — ці прапори дозволяють запускати рушій в інший режим (тільки для тестів).

---

## Встановлення/переключення WebView-провайдера
```bash
adb shell settings put global webview_provider com.google.android.webview
adb shell settings get global webview_provider
adb shell settings put global webview_provider com.android.chrome
adb reboot
```

**Навіщо:** примусити систему використовувати конкретну реалізацію WebView.

---

## Запуск конкретних Activity (deep launch)
```bash
adb shell am start -n com.example.app/com.example.app.ui.MainActivity
adb shell am start -n com.example.app/ua.com.example.bank.BankActivity
adb shell am start -n com.example.app/com.exponea.sdk.view.InAppMessageActivity
adb shell am start -n com.example.app/com.google.firebase.auth.internal.RecaptchaActivity
adb shell am start -a android.intent.action.VIEW -d "https://example.com/some/path" com.example.app
adb shell am start -a android.intent.action.MAIN -c android.intent.category.LAUNCHER -n com.example.app/com.example.app.ui.MainActivity
```

**Навіщо:** перевіряти, чи можна відкрити внутрішні екрани без повної авторизації.

---

## Робота з APK / manifest / шлях до APK
```bash
adb shell pm path com.example.app
adb pull $(adb shell pm path com.example.app | sed 's/package://') ./example.apk
aapt dump xmltree example.apk AndroidManifest.xml > manifest.txt
```

**Навіщо:** знайти активності/дозволи/intent-filter-и для deep-launch та аналізу.

---

## Доступ до sandbox / файлів застосунку
```bash
adb shell run-as com.example.app ls -l /data/data/com.example.app
adb shell run-as com.example.app ls -l /data/data/com.example.app/shared_prefs
adb shell run-as com.example.app cat /data/data/com.example.app/shared_prefs/mysettings.xml
adb shell run-as com.example.app ls -l /data/data/com.example.app/databases
adb shell run-as com.example.app cat /data/data/com.example.app/databases/app.db > /sdcard/app.db
adb pull /sdcard/app.db .
```

**Навіщо:** перевірити локально збережені налаштування, токени, SQLite бази, WebView cookies.

---

## Аналіз SQLite баз
```bash
sqlite3 app.db ".tables"
sqlite3 app.db "PRAGMA table_info(<table_name>);"
sqlite3 app.db "SELECT * FROM <table_name> LIMIT 5;"
sqlite3 app.db ".dump" | grep -E "eyJ[A-Za-z0-9_-]{10,}"
```

**Навіщо:** знайти JWT, access_token, refresh_token, authorization_code у базі.

---

## Швидкий grep/пошук токенів у sandbox
```bash
adb shell run-as com.example.app grep -R --binary-files=text -I "eyJ[a-zA-Z0-9_-]\{10,\}" /data/data/com.example.app || true
adb shell run-as com.example.app grep -R "token" /data/data/com.example.app 2>/dev/null || true
adb shell run-as com.example.app grep -R "auth" /data/data/com.example.app 2>/dev/null || true
```

**Навіщо:** швидко локалізувати файли, де зберігаються підозрілі значення.

---

## WebView cookie DB та localStorage
```bash
adb shell run-as com.example.app cat /data/data/com.example.app/app_webview/Default/Cookies > /sdcard/cookies.db
adb pull /sdcard/cookies.db .
sqlite3 cookies.db "SELECT host_key, name, value FROM cookies WHERE name LIKE '%token%' OR value LIKE '%eyJ%';"
```

**Навіщо:** cookies WebView можуть містити сесійні JWT / cookie.

---

## Видалення / очищення (тільки для тестів)
```bash
adb shell run-as com.example.app rm /data/data/com.example.app/app_webview/Default/Cookies
adb shell run-as com.example.app rm /data/data/com.example.app/files/PersistedInstallation*.json
```

**Навіщо:** перевірити реакцію апки на відсутність локальних токенів/сесій.

---

## UI-автоматизація (натиск/ввід)
```bash
adb shell input keyevent KEYCODE_BACK
adb shell input tap 500 1600
adb shell input text "test@example.com"
adb shell input keyevent 66
```

**Навіщо:** автоматичне натискання кнопок і заповнення полів при тестуванні.

---

## Аналіз логів / dumpsys
```bash
adb logcat -c
adb logcat | sed -n '1,200p'
adb shell dumpsys package com.example.app > dumpsys_example.txt
adb shell dumpsys activity activities | sed -n '/com.example.app/,/Hist/p'
```

**Навіщо:** відстежувати помилки при старті, зависання WebView, перевіряти активності.

### Показати поточну активну Activity
```bash
adb shell dumpsys activity activities | grep mResumedActivity
```
Повертає рядок з `mResumedActivity` — яка Activity зараз у фокусі.

### Коротко через dumpsys window
```bash
adb shell dumpsys window | grep mCurrentFocus
```
Показує поточне вікно / фокус — часто дає назву пакету та Activity.

### Повний дамп конкретної Activity
```bash
adb shell dumpsys activity com.example.app/ua.com.example.bank.BankActivity
```
Детальний дамп: стани Activity, FragmentManager, ViewHierarchy, saved state, аргументи фрагментів тощо.

### Глибший grep по Dump
```bash
adb shell dumpsys activity | grep -A 20 "BankActivity"
```
Виводить контекст навколо згадок `BankActivity` (потрібно, якщо хочеш більше рядків після знайденого).

---

## Робота з процесом / купою (heap) — пошук runtime-об'єктів

### Знайти PID процесу
```bash
adb shell pidof com.example.app
```
Або:
```bash
adb shell ps | grep com.example.app
```
Отримати PID потрібно для подальших операцій з дампом пам'яті.

### Зробити heap dump на пристрої
```bash
adb shell am dumpheap <PID> /data/local/tmp/heap.hprof
```
Або (для debuggable; з явним юзером):
```bash
adb shell am dumpheap --user 0 <PID> /data/local/tmp/heap.hprof
```
1. Відкрити heap-conv.hprof в Android Studio (Memory Profiler) або Eclipse MAT -> шукати `PinView`, `ChangePinFragment`.
2. Виконати `adb shell uiautomator dump` та переглянути `window_dump.xml` для перевірки id в UI.
3. Викликати Activity через `am start` з потрібними екстрами / deeplink.
4. Перевіряти `dumpsys activity ...` для підтвердження стану фрагментів.
Це робить дамп купи у файл на пристрої.

### Скачати дамп на хост і конвертувати
```bash
adb pull /data/local/tmp/heap.hprof .
hprof-conv heap.hprof heap-conv.hprof
```
`hprof-conv` з Android SDK конвертує формат у сумісний з MAT/Android Studio.

---

## Швидка інспекція UI-дерева

### UI Automator dump (XML)
```bash
adb shell uiautomator dump /sdcard/window_dump.xml
adb pull /sdcard/window_dump.xml .
```
Отримує XML з елементами UI, resource-id, видимим текстом (корисно для перевірки id `v_pin`, `b_1` тощо).

---

## 4. Виклик Activity / deeplink / intent-extras

> Наведені приклади — варіативні. Підставляй свій `card_id` та перевір точні імена екстр у коді/manifest.

### Deeplink (ACTION_VIEW)
```bash
adb shell am start -n com.example.app/ua.com.example.bank.BankActivity \
  -a android.intent.action.VIEW \
  -d "example://bank/change_pin?card_id=274465"
```
Спроба викликати екран через URI-scheme (якщо зареєстровано).

### Через extras (ціле число та рядок)
```bash
adb shell am start -n com.example.app/ua.com.example.bank.BankActivity \
  --ei card_id 274465 \
  --es fragment "ChangePinFragment"
```
Передає `card_id` як інтенг-екстра; `fragment` — умовний ключ.

### Інша форма для NavController
```bash
adb shell am start -n com.example.app/ua.com.example.bank.BankActivity \
  --es nav_destination "change_pin" \
  --ei card_id 274465
```

### Простий рядковий екстра
```bash
adb shell am start -n com.example.app/ua.com.example.bank.BankActivity \
  -e card_id 274465
```

### Як перевірити, що фрагмент відкрився
```bash
adb shell dumpsys activity com.example.app/ua.com.example.bank.BankActivity | grep -A 4 "ChangePinFragment"
```
Або:
```bash
adb shell dumpsys activity activities | grep ChangePinFragment -n
```

---

## 5. Робота з файлами всередині додатка (debuggable / емулятор)

### Виконувати команди від імені пакету (run-as)
```bash
adb shell run-as com.example.app ls /data/data/com.example.app/files
adb shell run-as com.example.app cat /data/data/com.example.app/shared_prefs/*.xml
```
Працює лише для debuggable-збірок або якщо у тебе права доступу в емуляторі.

---

## 6. Пошук у APK / Manifest (на хості)

> Потрібно мати `aapt` (Android build tools) або `jadx`/`apktool`.

### Перевірити AndroidManifest / intent-filters для Activity
```bash
aapt dump xmltree app.apk AndroidManifest.xml | grep -A 5 BankActivity
```

### Шукати згадки secrets у ресурсах / nav-graph
```bash
aapt dump xmltree app.apk | grep -i secrets
```

---

## 7. Додаткові корисні команди

### Переглянути останні логи (logcat)
```bash
adb logcat -s "com.example.app"   # або загальний adb logcat
```
Фільтруй по тегам (наприклад `DEV_PIN`, `BankActivity`) для швидкого пошуку.
---

## Завантаження додатку .apk
Потрібно спочатку дізнатись шлях до APK, а потім витягнути файл:

```bash
adb shell pm path com.example.app
```

```bash
adb pull /data/app/~~XYZ/base.apk ./com.example.app.apk
```

---
