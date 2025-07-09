import os
from PIL import Image

# Paths
input_dir = 'login_system/static/images'
output_dir = 'login_system/static/images_resized'
output_size = (256, 256)  # Resize target

# Ensure output folder exists
os.makedirs(output_dir, exist_ok=True)

# Process images
for filename in os.listdir(input_dir):
    if filename.lower().endswith(('.jpg', '.jpeg', '.png')):
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)

        try:
            with Image.open(input_path) as img:
                img = img.resize(output_size, Image.Resampling.LANCZOS)  # <— FIXED HERE
                img.save(output_path, optimize=True, quality=85)
                print(f"✅ Resized: {filename}")
        except Exception as e:
            print(f"❌ Error resizing {filename}: {e}")
