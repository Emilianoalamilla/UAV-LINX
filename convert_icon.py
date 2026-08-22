from PIL import Image
import os

png_path = "assets/icon.png"
ico_path = "assets/icon.ico"

if os.path.exists(png_path):
    img = Image.open(png_path)
    img.save(ico_path, format="ICO")
    print(f"Converted {png_path} to {ico_path}")
else:
    print(f"File not found: {png_path}")
