from app.services.ocr_service import preprocess_image, extract_text, parse_chart_metadata

import os

image_path = os.path.join(os.path.dirname(__file__), "test_image", "image.png")

processed = preprocess_image(image_path)
texts = extract_text(processed)

print("Raw detected text:")
for t in texts:
    print(f"  - {t}")

metadata = parse_chart_metadata(texts)
print("\nParsed metadata:", metadata)