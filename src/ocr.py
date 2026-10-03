import sys
import cv2
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

def preprocess(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image introuvable : {path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.medianBlur(gray, 3)
    return cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
def read_text(path):
    img = cv2.imread(path)
    if img is None:
        raise FileNotFoundError(f"Image introuvable : {path}")
    img = cv2.resize(img, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return pytesseract.image_to_string(gray, lang="fra", config="--psm 6")
if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "data/ordonnances/test1.png"
    print(read_text(path))