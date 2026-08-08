"""Script to crop the GeoTutor logo and make background transparent."""
import sys
sys.path.insert(0, r'e:\YORK.A\Python codes2\Antigrav\.venv\Lib\site-packages')

from PIL import Image

# Open the original logo
input_path = r'C:\Users\pierr\.gemini\antigravity\brain\9ea8a298-bb20-426d-a635-5629d080dfee\uploaded_image_2_1767930466961.png'
output_path = r'e:\YORK.A\Python codes2\Antigrav\geotutor\client\public\geotutor-logo.png'

img = Image.open(input_path)
print(f"Original size: {img.size}, Mode: {img.mode}")

# Convert to RGBA if needed
if img.mode != 'RGBA':
    img = img.convert('RGBA')

# Make white pixels transparent
datas = img.getdata()
new_data = []
for item in datas:
    # If pixel is white or near-white, make it transparent
    if item[0] > 240 and item[1] > 240 and item[2] > 240:
        new_data.append((255, 255, 255, 0))  # Transparent
    else:
        new_data.append(item)

img.putdata(new_data)

# Get bounding box of non-transparent pixels
bbox = img.getbbox()
print(f"Bounding box: {bbox}")

# Crop to bounding box with small padding
if bbox:
    padding = 5
    left = max(0, bbox[0] - padding)
    top = max(0, bbox[1] - padding)
    right = min(img.width, bbox[2] + padding)
    bottom = min(img.height, bbox[3] + padding)
    img = img.crop((left, top, right, bottom))

print(f"Cropped size: {img.size}")

# Save the processed image
img.save(output_path, 'PNG')
print(f"Saved to: {output_path}")
