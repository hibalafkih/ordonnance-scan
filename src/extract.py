import re

def extract_meds(text):
    meds = []
    for line in text.splitlines():
        m = re.search(r"([A-Za-zÀ-ÿ]{4,})\s+(\d+(?:[.,]\d+)?)\s*(mg|g|ml|µg|ui)\b",
                      line, re.IGNORECASE)
        if m:
            meds.append({"nom": m.group(1).capitalize(),
                         "dosage": f"{m.group(2)} {m.group(3).lower()}"})
    return meds

if __name__ == "__main__":
    from ocr import read_text
    print(extract_meds(read_text("data/ordonnances/test1.png")))