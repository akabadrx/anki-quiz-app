import os
from PIL import Image

# Folder containing your images
source_folder = 'login_system/static/images_resized'

for filename in os.listdir(source_folder):
    file_path = os.path.join(source_folder, filename)
    
    # Skip non-files
    if not os.path.isfile(file_path):
        continue

    # Get file name without extension
    name, ext = os.path.splitext(filename)
    ext = ext.lower()

    # Skip if already .jpg (lowercase only)
    if ext == '.jpg':
        continue

    try:
        # Open and convert image to RGB
        with Image.open(file_path) as img:
            rgb_img = img.convert('RGB')
            new_path = os.path.join(source_folder, f"{name}.jpg")
            rgb_img.save(new_path, format='JPEG')
            print(f"✅ Converted: {filename} → {name}.jpg")

        # Delete the old file
        os.remove(file_path)
    except Exception as e:
        print(f"❌ Error converting {filename}: {e}")
