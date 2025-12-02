import os
from PIL import Image

# مجلد الصور الأصلية
input_folder = 'login_system/static/images'
# مجلد الصور المصغرة
output_folder = 'login_system/static/images_resized'

# تأكد أن مجلد الإخراج موجود
os.makedirs(output_folder, exist_ok=True)
 
# الحجم المطلوب
target_size = (400, 400)

for filename in os.listdir(input_folder):
    input_path = os.path.join(input_folder, filename)

    if not os.path.isfile(input_path):
        continue

    try:
        # افتح الصورة وحولها إلى RGB
        with Image.open(input_path) as img:
            img = img.convert("RGB")
            img_resized = img.resize(target_size)

            # اسم الملف بدون الامتداد
            name_without_ext = os.path.splitext(filename)[0]
            output_path = os.path.join(output_folder, f"{name_without_ext}.jpg")

            # احفظ الصورة بصيغة JPG
            img_resized.save(output_path, format='JPEG')
            print(f"✅ {filename} → {output_path}")
    except Exception as e:
        print(f"❌ Error processing {filename}: {e}")
